"""
QR Code Detection Module
Real-time webcam capture with HSV color segmentation for color-coded QR codes
"""

import cv2
import numpy as np
import time
from typing import Tuple, Optional, List
import logging
from config import COLOR_THRESHOLDS, QR_DETECTION, QRDET_SETTINGS
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

            # Apply adaptive thresholding
            gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

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
    
    
    
    
    def stop_detection(self):
        """Stop QR code detection and release resources"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.logger.info("QR detection stopped")
    

