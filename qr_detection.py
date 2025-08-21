"""
QR Code Detection Module
Real-time webcam capture with HSV color segmentation for color-coded QR codes
"""

import cv2
import numpy as np
import time
from typing import Tuple, Optional, List
import logging
from config import COLOR_THRESHOLDS, QR_DETECTION, YOLO_SETTINGS, QRDET_SETTINGS
try:
    from ultralytics import YOLO  # type: ignore
except Exception:
    YOLO = None  # type: ignore
try:
    from qrdet import QRDetector  # type: ignore
except Exception:
    QRDetector = None  # type: ignore

class QRCodeDetector:
    """Real-time QR code detection using color segmentation and size thresholds"""
    
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.detected_colors = []
        self.qr_regions = []
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize QR detector once for better performance
        self.qr_detector = cv2.QRCodeDetector()
        
        # Optional YOLO model for region proposals
        self.yolo_model = None
        if YOLO_SETTINGS.get('enabled', False) and YOLO is not None:
            weights_path = YOLO_SETTINGS.get('weights_path', 'models/qr_yolo.pt')
            try:
                self.yolo_model = YOLO(weights_path)
                self.logger.info(f"YOLO model loaded from {weights_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load YOLO model: {e}")
                self.yolo_model = None

        # Optional QRDet model for specialized QR detection
        self.qrdet_model = None
        if QRDET_SETTINGS.get('enabled', False) and QRDetector is not None:
            try:
                self.qrdet_model = QRDetector(
                    model_size=QRDET_SETTINGS.get('model_size', 's'),
                    conf_th=float(QRDET_SETTINGS.get('conf_th', 0.5)),
                    nms_iou=float(QRDET_SETTINGS.get('nms_iou', 0.3))
                )
                self.logger.info("QRDet model initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize QRDet: {e}")
                self.qrdet_model = None
        
        # Initialize camera
        self._init_camera()
    
    def _init_camera(self):
        """Initialize webcam capture"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera {self.camera_index}")
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.logger.info("Camera initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Camera initialization failed: {e}")
            raise
    
    def _create_color_mask(self, frame: np.ndarray, color: str) -> np.ndarray:
        """Create binary mask for specified color using HSV thresholds"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        if color == 'red':
            # Red wraps around HSV circle, need two masks
            lower1 = np.array(COLOR_THRESHOLDS['red']['lower1'])
            upper1 = np.array(COLOR_THRESHOLDS['red']['upper1'])
            lower2 = np.array(COLOR_THRESHOLDS['red']['lower2'])
            upper2 = np.array(COLOR_THRESHOLDS['red']['upper2'])
            
            mask1 = cv2.inRange(hsv, lower1, upper1)
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = mask1 + mask2
            
        else:
            lower = np.array(COLOR_THRESHOLDS[color]['lower'])
            upper = np.array(COLOR_THRESHOLDS[color]['upper'])
            mask = cv2.inRange(hsv, lower, upper)
        
        # Apply morphological operations to clean up the mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask
    
    def _find_color_regions(self, frame: np.ndarray) -> List[Tuple[str, np.ndarray, Tuple[int, int, int, int]]]:
        """Find regions via HSV color masks. Returns list of (color, roi, bbox)."""
        proposals: List[Tuple[str, np.ndarray, Tuple[int, int, int, int]]] = []
        for color in ['red', 'green', 'blue']:
            mask = self._create_color_mask(frame, color)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:
                    x, y, w, h = cv2.boundingRect(contour)
                    if (QR_DETECTION['min_size'] <= w <= QR_DETECTION['max_size'] and 
                        QR_DETECTION['min_size'] <= h <= QR_DETECTION['max_size']):
                        roi = frame[y:y+h, x:x+w]
                        proposals.append((color, roi, (x, y, w, h)))
        return proposals

    def _find_yolo_regions(self, frame: np.ndarray) -> List[Tuple[str, np.ndarray, Tuple[int, int, int, int]]]:
        """Use YOLO to propose QR bounding boxes. Returns list of (label, roi, bbox)."""
        results_list: List[Tuple[str, np.ndarray, Tuple[int, int, int, int]]] = []
        if self.yolo_model is None:
            return results_list
        try:
            results = self.yolo_model.predict(
                source=frame,
                imgsz=YOLO_SETTINGS.get('img_size', 640),
                conf=YOLO_SETTINGS.get('conf_threshold', 0.25),
                iou=YOLO_SETTINGS.get('iou_threshold', 0.45),
                max_det=YOLO_SETTINGS.get('max_det', 50),
                verbose=False
            )
            # Expect one result for single image
            if not results:
                return results_list
            res = results[0]
            if not hasattr(res, 'boxes'):
                return results_list
            h, w = frame.shape[:2]
            for b in res.boxes:
                try:
                    xyxy = b.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    x1, y1, x2, y2 = [int(max(0, v)) for v in xyxy]
                    x1, y1 = min(x1, w-1), min(y1, h-1)
                    x2, y2 = min(max(x2, x1+1), w), min(max(y2, y1+1), h)
                    bw, bh = x2 - x1, y2 - y1
                    if bw < QR_DETECTION['min_size'] or bh < QR_DETECTION['min_size']:
                        continue
                    roi = frame[y1:y2, x1:x2]
                    # Use generic label 'yolo'
                    results_list.append(('yolo', roi, (x1, y1, bw, bh)))
                except Exception:
                    continue
        except Exception as e:
            self.logger.warning(f"YOLO inference failed: {e}")
        return results_list

    def _find_qrdet_regions(self, frame: np.ndarray) -> List:
        """Use QRDet to propose QR bounding boxes.
        Returns tuples: ('qrdet', roi, bbox[, quad_xy])
        """
        results_list: List = []
        if self.qrdet_model is None:
            return results_list
        try:
            detections = self.qrdet_model.detect(image=frame, is_bgr=True)
            h, w = frame.shape[:2]
            for det in detections:
                x1, y1, x2, y2 = det.get('bbox_xyxy', [0, 0, 0, 0])
                x1, y1, x2, y2 = int(max(0, x1)), int(max(0, y1)), int(x2), int(y2)
                x1, y1 = min(x1, w-1), min(y1, h-1)
                x2, y2 = min(max(x2, x1+1), w), min(max(y2, y1+1), h)
                bw, bh = x2 - x1, y2 - y1
                # Allow slightly smaller proposals to help distant QRs
                min_size = max(50, QR_DETECTION['min_size'])
                if bw < min_size or bh < min_size:
                    continue
                roi = frame[y1:y2, x1:x2]
                quad = det.get('quad_xy', None)
                if quad is not None:
                    results_list.append(('qrdet', roi, (x1, y1, bw, bh), np.array(quad)))
                else:
                    results_list.append(('qrdet', roi, (x1, y1, bw, bh)))
        except Exception as e:
            self.logger.warning(f"QRDet inference failed: {e}")
        return results_list
    
    def _detect_qr_in_region(self, region: np.ndarray) -> bool:
        """Check if a region contains a QR code using OpenCV's QR detector"""
        try:
            # Try original region first
            data, bbox, _ = self.qr_detector.detectAndDecode(region)
            if data != "" and bbox is not None:
                return True
            
            # If original fails, try with preprocessing
            # Convert to grayscale
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            data, bbox, _ = self.qr_detector.detectAndDecode(gray)
            if data != "" and bbox is not None:
                return True
            
            # Try with resized region (2x larger)
            height, width = region.shape[:2]
            resized = cv2.resize(region, (width * 2, height * 2))
            data, bbox, _ = self.qr_detector.detectAndDecode(resized)
            if data != "" and bbox is not None:
                return True
            
            # Try with contrast enhancement
            lab = cv2.cvtColor(region, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            cl = clahe.apply(l)
            enhanced = cv2.merge((cl,a,b))
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            data, bbox, _ = self.qr_detector.detectAndDecode(enhanced)
            if data != "" and bbox is not None:
                return True
            
            return False
        except Exception as e:
            self.logger.debug(f"QR detection error: {e}")
            return False

    def _warp_from_quad(self, frame: np.ndarray, quad_xy: np.ndarray, side: int = 320) -> Optional[np.ndarray]:
        """Warp a quadrilateral region to a square patch for easier decoding."""
        try:
            if quad_xy is None or len(quad_xy) != 4:
                return None
            h, w = frame.shape[:2]
            src = quad_xy.astype('float32')
            src[:, 0] = np.clip(src[:, 0], 0, w - 1)
            src[:, 1] = np.clip(src[:, 1], 0, h - 1)
            # Order points by angle around centroid to roughly TL, TR, BR, BL
            cx, cy = float(np.mean(src[:, 0])), float(np.mean(src[:, 1]))
            angles = np.arctan2(src[:, 1] - cy, src[:, 0] - cx)
            order = np.argsort(angles)
            src = src[order]
            dst = np.array([[0, 0], [side - 1, 0], [side - 1, side - 1], [0, side - 1]], dtype='float32')
            M = cv2.getPerspectiveTransform(src, dst)
            warped = cv2.warpPerspective(frame, M, (side, side))
            return warped
        except Exception:
            return None
    
    def start_detection(self):
        """Start real-time QR code detection"""
        if self.cap is None:
            raise RuntimeError("Camera not initialized")
        
        self.is_running = True
        self.logger.info("Starting QR code detection...")
        
        try:
            while self.is_running:
                ret, frame = self.cap.read()
                if not ret:
                    self.logger.warning("Failed to read frame from camera")
                    continue
                
                self.current_frame = frame.copy()
                
                # Find regions via color and optionally YOLO
                color_regions = self._find_color_regions(frame)
                yolo_regions = self._find_yolo_regions(frame) if self.yolo_model is not None else []
                qrdet_regions = self._find_qrdet_regions(frame) if self.qrdet_model is not None else []
                all_regions = color_regions + yolo_regions + qrdet_regions
                
                # Check each region for QR codes
                detected_qrs = []
                for color, roi, bbox in all_regions:
                    if self._detect_qr_in_region(roi):
                        detected_qrs.append((color, roi, bbox))
                        self.logger.info(f"QR code detected in {color} region at {bbox}")
                
                # Update detected QR codes
                self.qr_regions = detected_qrs
                
                # Draw detection results on frame
                self._draw_detection_results(frame, all_regions, detected_qrs)
                
                # Display frame
                cv2.imshow('QR Code Detection', frame)
                
                # Check for key press to exit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
        except KeyboardInterrupt:
            self.logger.info("Detection stopped by user")
        finally:
            self.stop_detection()
    
    def _draw_detection_results(self, frame: np.ndarray, color_regions: List, detected_qrs: List):
        """Draw detection results on the frame for visualization"""
        # Draw all color regions
        for color, roi, (x, y, w, h) in color_regions:
            color_bgr = {
                'red': (0, 0, 255),
                'green': (0, 255, 0),
                'blue': (255, 0, 0)
            }[color]
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), color_bgr, 2)
            cv2.putText(frame, color, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_bgr, 2)
        
        # Highlight detected QR codes
        for color, roi, (x, y, w, h) in detected_qrs:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 3)
            cv2.putText(frame, f"QR: {color}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the current frame for external processing"""
        return self.current_frame
    
    def get_detected_qrs(self) -> List:
        """Get list of currently detected QR codes"""
        return self.qr_regions
    
    def is_qr_detected(self) -> bool:
        """Check if any QR code is currently detected"""
        return len(self.qr_regions) > 0
    
    def stop_detection(self):
        """Stop QR code detection and release resources"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.logger.info("QR detection stopped")
    
    def calibrate_hsv(self, color: str, sample_frame: np.ndarray):
        """Fast HSV calibration for improved color detection"""
        self.logger.info(f"Starting HSV calibration for {color}")
        
        # Create trackbars for HSV adjustment
        window_name = f"HSV Calibration - {color}"
        cv2.namedWindow(window_name)
        
        # Initialize trackbar values
        h_min, s_min, v_min = COLOR_THRESHOLDS[color]['lower']
        h_max, s_max, v_max = COLOR_THRESHOLDS[color]['upper']
        
        def nothing(x):
            pass
        
        cv2.createTrackbar('H_min', window_name, h_min, 179, nothing)
        cv2.createTrackbar('S_min', window_name, s_min, 255, nothing)
        cv2.createTrackbar('V_min', window_name, v_min, 255, nothing)
        cv2.createTrackbar('H_max', window_name, h_max, 179, nothing)
        cv2.createTrackbar('S_max', window_name, s_max, 255, nothing)
        cv2.createTrackbar('V_max', window_name, v_max, 255, nothing)
        
        while True:
            h_min = cv2.getTrackbarPos('H_min', window_name)
            s_min = cv2.getTrackbarPos('S_min', window_name)
            v_min = cv2.getTrackbarPos('V_min', window_name)
            h_max = cv2.getTrackbarPos('H_max', window_name)
            s_max = cv2.getTrackbarPos('S_max', window_name)
            v_max = cv2.getTrackbarPos('V_max', window_name)
            
            # Create mask with current values
            hsv = cv2.cvtColor(sample_frame, cv2.COLOR_BGR2HSV)
            lower = np.array([h_min, s_min, v_min])
            upper = np.array([h_max, s_max, v_max])
            mask = cv2.inRange(hsv, lower, upper)
            
            # Show result
            result = cv2.bitwise_and(sample_frame, sample_frame, mask=mask)
            cv2.imshow('Calibration Result', result)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):  # Save calibration
                COLOR_THRESHOLDS[color]['lower'] = [h_min, s_min, v_min]
                COLOR_THRESHOLDS[color]['upper'] = [h_max, s_max, v_max]
                self.logger.info(f"HSV calibration saved for {color}")
                break
            elif key == ord('q'):  # Quit without saving
                break
        
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Test the QR detector
    detector = QRCodeDetector()
    try:
        detector.start_detection()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        detector.stop_detection()
