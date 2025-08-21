#!/usr/bin/env python3
"""
Test script for voice system functionality
"""

import sys
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    import pyttsx3
    print("✓ pyttsx3 imported successfully")
except ImportError as e:
    print(f"✗ Failed to import pyttsx3: {e}")
    sys.exit(1)

def test_pyttsx3_basic():
    """Test basic pyttsx3 functionality"""
    print("\n=== Testing Basic pyttsx3 ===")
    
    try:
        # Initialize engine
        engine = pyttsx3.init()
        print("✓ Engine initialized")
        
        # Get voices
        voices = engine.getProperty('voices')
        print(f"✓ Found {len(voices)} voices")
        
        for i, voice in enumerate(voices):
            print(f"  Voice {i}: {voice.name} ({voice.id})")
        
        # Set properties
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.9)
        print("✓ Properties set")
        
        # Test speech
        print("Speaking test message...")
        engine.say("This is a test of the voice system")
        engine.runAndWait()
        print("✓ Basic speech test completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic test failed: {e}")
        return False

def test_voice_speaker():
    """Test the AutoVoiceSpeaker class"""
    print("\n=== Testing AutoVoiceSpeaker ===")
    
    try:
        from user_interface import AutoVoiceSpeaker
        
        speaker = AutoVoiceSpeaker()
        print(f"✓ AutoVoiceSpeaker created, available: {speaker.available}")
        
        if speaker.available:
            print("Testing speech...")
            speaker.speak("AutoVoiceSpeaker test message", priority=True)
            time.sleep(3)  # Wait for speech to complete
            
            print("Testing queue...")
            speaker.speak("First queued message")
            speaker.speak("Second queued message")
            speaker.speak("Third queued message")
            time.sleep(5)  # Wait for queue to process
            
            speaker.shutdown()
            print("✓ AutoVoiceSpeaker test completed")
            return True
        else:
            print("✗ AutoVoiceSpeaker not available")
            return False
            
    except Exception as e:
        print(f"✗ AutoVoiceSpeaker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_feedback():
    """Test the AudioFeedback class"""
    print("\n=== Testing AudioFeedback ===")
    
    try:
        from audio_feedback import AudioFeedback
        
        audio = AudioFeedback()
        print(f"✓ AudioFeedback created, initialized: {audio.is_initialized}")
        
        if audio.is_initialized:
            print("Testing speech...")
            audio.speak("AudioFeedback test message", priority=True)
            time.sleep(3)  # Wait for speech to complete
            
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
    """Run all voice system tests"""
    print("Voice System Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test basic pyttsx3
    results.append(("Basic pyttsx3", test_pyttsx3_basic()))
    
    # Test AutoVoiceSpeaker
    results.append(("AutoVoiceSpeaker", test_voice_speaker()))
    
    # Test AudioFeedback
    results.append(("AudioFeedback", test_audio_feedback()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\nThe voice system appears to be working correctly.")
        print("If you're still not hearing audio in the main application,")
        print("the issue might be related to the GUI threading or audio device conflicts.")
    else:
        print("\nSome voice system components are not working.")
        print("Please check your audio settings and pyttsx3 installation.")

if __name__ == "__main__":
    main()
