"""
বাংলা থেকে ইংরেজি ফোন নম্বর কনভার্শন টেস্ট
Test script for Bangla to English phone number conversion
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our phone utilities
from orders.phone_utils import convert_bangla_to_english_digits, normalize_bangladeshi_phone

def test_bangla_conversion():
    """Test Bangla to English digit conversion"""
    print("🧪 বাংলা থেকে ইংরেজি সংখ্যা কনভার্শন টেস্ট")
    print("=" * 60)
    
    test_cases = [
        ("০১৭৭৭১৭৩০৪০", "01777173040"),
        ("০১৮৮৮১২৩৪৫৬", "01888123456"),
        ("০১৯৯৯৮৮৭৭৬৬", "01999887766"),  # Fixed: removed incorrect character
        ("০১৫৫৫৬৬৬৭৭৭", "01555666777"),
        ("০১৩১২৩৪৫৬৭৮", "01312345678"),
        ("+৮৮০১৭৭৭১৭৩০৪০", "+8801777173040"),
        ("৮৮০১৮৮৮১২৩৪৫৬", "8801888123456"),
        ("০১৭৭৭-১৭৩০৪০", "01777-173040"),
        ("০১৭৭৭ ১৭৩০৪০", "01777 173040"),
        ("মিশ্র: ০১৭৭৭abc১৭৩০৪০", "মিশ্র: 01777abc173040")
    ]
    
    all_passed = True
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = convert_bangla_to_english_digits(input_text)
        passed = result == expected
        
        status = "✅ পাস" if passed else "❌ ফেইল"
        print(f"টেস্ট {i:2d}: {status}")
        print(f"   ইনপুট:    {input_text}")
        print(f"   আউটপুট:   {result}")
        print(f"   প্রত্যাশিত: {expected}")
        
        if not passed:
            all_passed = False
            print(f"   ❌ মিল নেই!")
        print()
    
    return all_passed

def test_phone_normalization():
    """Test complete phone number normalization"""
    print("📱 ফোন নম্বর নরমালাইজেশন টেস্ট")
    print("=" * 60)
    
    test_cases = [
        ("০১৭৭৭১৭৩০৪০", "01777173040"),
        ("০১৮৮৮১২৩৪৫৬", "01888123456"),
        ("০১৯৯৯৮৮৭৭৬৬", "01999887766"),
        ("+৮৮০১৭৭৭১৭৩০৪০", "01777173040"),
        ("৮৮০১৮৮৮১২৩৪৫৬", "01888123456"),
        ("০১৭৭৭-১৭৩০৪০", "01777173040"),
        ("০১৭৭৭ ১৭৩০৪০", "01777173040"),
        ("1777173040", "01777173040"),  # Missing leading 0
        ("8801777173040", "01777173040"),  # 88 prefix
        ("+8801777173040", "01777173040")  # +88 prefix
    ]
    
    all_passed = True
    
    for i, (input_phone, expected) in enumerate(test_cases, 1):
        result = normalize_bangladeshi_phone(input_phone)
        passed = result == expected
        
        status = "✅ পাস" if passed else "❌ ফেইল"
        print(f"টেস্ট {i:2d}: {status}")
        print(f"   ইনপুট:    {input_phone}")
        print(f"   আউটপুট:   {result}")
        print(f"   প্রত্যাশিত: {expected}")
        
        if not passed:
            all_passed = False
            print(f"   ❌ মিল নেই!")
        print()
    
    return all_passed

def test_mixed_input():
    """Test mixed Bangla-English input"""
    print("🔀 মিশ্র ইনপুট টেস্ট")
    print("=" * 60)
    
    test_cases = [
        ("০1৭77১7৩0৪0", "01777173040"),  # Mixed digits
        ("০১৭৭৭173040", "01777173040"),   # Partial Bangla
        ("01৭৭৭১৭৩০৪০", "01777173040"),   # Partial English
    ]
    
    all_passed = True
    
    for i, (input_phone, expected) in enumerate(test_cases, 1):
        # First convert digits
        converted = convert_bangla_to_english_digits(input_phone)
        # Then normalize
        result = normalize_bangladeshi_phone(converted)
        passed = result == expected
        
        status = "✅ পাস" if passed else "❌ ফেইল"
        print(f"টেস্ট {i:2d}: {status}")
        print(f"   ইনপুট:      {input_phone}")
        print(f"   কনভার্ট:     {converted}")
        print(f"   নরমালাইজ:   {result}")
        print(f"   প্রত্যাশিত:  {expected}")
        
        if not passed:
            all_passed = False
            print(f"   ❌ মিল নেই!")
        print()
    
    return all_passed

def test_edge_cases():
    """Test edge cases"""
    print("⚠️  এজ কেস টেস্ট")
    print("=" * 60)
    
    test_cases = [
        ("", ""),  # Empty string
        ("০", "0"),  # Single digit
        ("০১", "01"),  # Two digits
        ("০১৭৭৭১৭৩০৪০৫৬৭৮", "017771730405678"),  # Too long - keeping digits only
    ]
    
    all_passed = True
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = convert_bangla_to_english_digits(input_text)
        passed = result == expected
        
        status = "✅ পাস" if passed else "❌ ফেইল"
        print(f"টেস্ট {i:2d}: {status}")
        print(f"   ইনপুট:    '{input_text}'")
        print(f"   আউটপুট:   '{result}'")
        print(f"   প্রত্যাশিত: '{expected}'")
        
        if not passed:
            all_passed = False
            print(f"   ❌ মিল নেই!")
        print()
    
    return all_passed

def main():
    """Run all tests"""
    print("🎯 বাংলা ফোন নম্বর কনভার্শন সিস্টেম টেস্ট")
    print("=" * 80)
    print()
    
    results = []
    
    # Run digit conversion tests
    results.append(test_bangla_conversion())
    print()
    
    # Run phone normalization tests
    results.append(test_phone_normalization())
    print()
    
    # Run mixed input tests
    results.append(test_mixed_input())
    print()
    
    # Run edge case tests
    results.append(test_edge_cases())
    print()
    
    # Summary
    print("📊 টেস্ট সারসংক্ষেপ")
    print("=" * 60)
    
    all_passed = all(results)
    total_tests = len(results)
    passed_tests = sum(results)
    
    print(f"মোট টেস্ট গ্রুপ: {total_tests}")
    print(f"পাস হয়েছে: {passed_tests}")
    print(f"ফেইল হয়েছে: {total_tests - passed_tests}")
    
    if all_passed:
        print("\n🎉 সব টেস্ট সফলভাবে পাস হয়েছে!")
        print("✅ বাংলা থেকে ইংরেজি ফোন নম্বর কনভার্শন সিস্টেম সম্পূর্ণ কাজ করছে।")
    else:
        print(f"\n❌ কিছু টেস্ট ফেইল হয়েছে। দয়া করে কোড পরীক্ষা করুন।")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)