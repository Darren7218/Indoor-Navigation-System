#!/usr/bin/env python3
"""
Simple voice test to isolate the issue
"""

import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_direct_pyttsx3():
    """Test pyttsx3 directly"""
    print("=== Testing pyttsx3 directly ===")
    try:
        import pyttsx3
        
        # Initialize engine
        engine = pyttsx3.init(driverName='sapi5')
        print("✓ Engine initialized")
        
        # Set properties
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 1.0)
        print("✓ Properties set")
        
        # Test speech
        print("Speaking test message...")
        engine.say("This is a direct pyttsx3 test. If you hear this, pyttsx3 is working.")
        engine.runAndWait()
        print("✓ Direct pyttsx3 test completed")
        
        return True
    except Exception as e:
        print(f"✗ Direct pyttsx3 test failed: {e}")
        return False

def test_audio_feedback():
    """Test AudioFeedback class"""
    print("\n=== Testing AudioFeedback class ===")
    try:
        from audio_feedback import AudioFeedback
        
        audio = AudioFeedback()
        print(f"✓ AudioFeedback created, initialized: {audio.is_initialized}")
        
        # Wait for initialization
        max_wait = 5
        wait_time = 0
        while not audio.is_initialized and wait_time < max_wait:
            time.sleep(0.5)
            wait_time += 0.5
            print(f"Waiting for initialization... ({wait_time}s)")
        
        if audio.is_initialized:
            print("✓ AudioFeedback initialized")
            
            # Test speech
            print("Speaking test message...")
            audio.speak("This is an AudioFeedback test. If you hear this, AudioFeedback is working.", priority=True)
            time.sleep(3)
            
            audio.shutdown()
            print("✓ AudioFeedback test completed")
            return True
        else:
            print("✗ AudioFeedback not initialized")
            return False
            
    except Exception as e:
        print(f"✗ AudioFeedback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the simple voice tests"""
    print("Simple Voice Test")
    print("=" * 50)
    
    # Test 1: Direct pyttsx3
    result1 = test_direct_pyttsx3()
    
    # Test 2: AudioFeedback
    result2 = test_audio_feedback()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    print(f"Direct pyttsx3: {'✓ PASS' if result1 else '✗ FAIL'}")
    print(f"AudioFeedback: {'✓ PASS' if result2 else '✗ FAIL'}")
    
    if result1 and result2:
        print("\n✓ Both tests passed! Voice system is working.")
        print("If you didn't hear speech, check your audio device settings.")
    elif result1 and not result2:
        print("\n⚠ Direct pyttsx3 works but AudioFeedback doesn't.")
        print("This suggests an issue with the AudioFeedback implementation.")
    elif not result1:
        print("\n✗ Direct pyttsx3 failed. This is a system-level issue.")
        print("Check your Windows TTS settings and audio device.")

if __name__ == "__main__":
    main()
