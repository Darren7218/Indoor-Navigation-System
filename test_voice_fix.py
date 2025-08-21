#!/usr/bin/env python3
"""
Test script to verify the voice system fix
"""

import sys
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_unified_audio():
    """Test the unified audio feedback approach"""
    print("Testing unified audio feedback...")
    
    try:
        from audio_feedback import AudioFeedback
        
        # Create audio feedback instance
        audio = AudioFeedback()
        print(f"AudioFeedback initialized: {audio.is_initialized}")
        
        # Wait for initialization (up to 5 seconds)
        max_wait = 5
        wait_time = 0
        while not audio.is_initialized and wait_time < max_wait:
            time.sleep(0.5)
            wait_time += 0.5
            print(f"Waiting for initialization... ({wait_time}s)")
        
        print(f"After waiting: AudioFeedback initialized: {audio.is_initialized}")
        
        if audio.is_initialized:
            # Test basic speech
            print("Testing basic speech...")
            audio.speak("This is a test of the unified audio system", priority=True)
            time.sleep(2)
            
            # Test multiple messages
            print("Testing multiple messages...")
            audio.speak("First message")
            audio.speak("Second message")
            audio.speak("Third message")
            time.sleep(5)
            
            # Test priority
            print("Testing priority message...")
            audio.speak("This is a priority message", priority=True)
            time.sleep(2)
            
            audio.shutdown()
            print("✓ Unified audio test completed successfully")
            return True
        else:
            print("✗ AudioFeedback not initialized after waiting")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_route_simulation():
    """Simulate route calculation and voice instructions"""
    print("\nTesting route voice instructions simulation...")
    
    try:
        from audio_feedback import AudioFeedback
        
        audio = AudioFeedback()
        
        # Wait for initialization (up to 5 seconds)
        max_wait = 5
        wait_time = 0
        while not audio.is_initialized and wait_time < max_wait:
            time.sleep(0.5)
            wait_time += 0.5
            print(f"Waiting for initialization... ({wait_time}s)")
        
        print(f"After waiting: AudioFeedback initialized: {audio.is_initialized}")
        
        if audio.is_initialized:
            # Simulate route info
            route_info = {
                'destination': {
                    'description': 'Lecture Room 1'
                },
                'instructions': [
                    'Walk straight ahead for 10 meters',
                    'Turn left at the corridor',
                    'Continue for 5 meters to reach your destination'
                ]
            }
            
            print("Speaking route instructions...")
            
            # Test with a simple message first
            audio.speak("Route calculation complete", priority=True)
            time.sleep(1)
            
            # Speak route summary
            route_summary = f"Route to {route_info['destination']['description']} calculated. Starting navigation instructions."
            audio.speak(route_summary, priority=True)
            time.sleep(2)
            
            # Speak each instruction
            instructions = route_info.get('instructions', [])
            for i, instruction in enumerate(instructions, 1):
                instruction_text = f"Step {i}: {instruction}"
                audio.speak(instruction_text)
                time.sleep(1)
            
            # Speak completion message
            completion_msg = "Navigation instructions complete. Follow the steps to reach your destination."
            audio.speak(completion_msg)
            time.sleep(2)
            
            audio.shutdown()
            print("✓ Route simulation completed successfully")
            return True
        else:
            print("✗ AudioFeedback not initialized after waiting")
            return False
            
    except Exception as e:
        print(f"✗ Route simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the voice fix tests"""
    print("Voice System Fix Test")
    print("=" * 40)
    
    results = []
    
    # Test unified audio
    results.append(("Unified Audio", test_unified_audio()))
    
    # Test route simulation
    results.append(("Route Simulation", test_route_simulation()))
    
    # Summary
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\nThe voice system fix appears to be working correctly.")
        print("You should now hear audio when calculating routes in the main application.")
    else:
        print("\nSome tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
