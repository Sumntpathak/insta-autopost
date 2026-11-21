"""DSA episodes 4-23 (same format as problems.py). Statements are written in our own words."""


def contains_duplicate(nums):
    seen = set()
    for i, x in enumerate(nums):
        if x in seen:
            return True
        seen.add(x)
    return False


def max_subarray(nums):
    cur = best = nums[0]
    for i in range(1, len(nums)):
        cur = max(nums[i], cur + nums[i])
        best = max(best, cur)
    return best


def missing_number(nums):
    total = len(nums) * (len(nums) + 1) // 2
    for i, x in enumerate(nums):
        total -= x
    return total


def single_number(nums):
    ans = 0
    for i, x in enumerate(nums):
        ans ^= x
    return ans


def majority(nums):
    cand, count = nums[0], 0
    for i, x in enumerate(nums):
        if count == 0:
            cand = x
        count += 1 if x == cand else -1
    return cand


def house_robber(nums):
    take, skip = 0, 0
    for i, x in enumerate(nums):
        take, skip = skip + x, max(take, skip)
    return max(take, skip)


def search_insert(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return lo


def find_peak(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < nums[mid + 1]:
            lo = mid + 1
        else:
            hi = mid
    return lo


def two_sum_sorted(nums, target):
    l, r = 0, len(nums) - 1
    while l < r:
        total = nums[l] + nums[r]
        if total == target:
            return [l, r]
        if total < target:
            l += 1
        else:
            r -= 1
    return []


def max_water(nums):
    l, r, best = 0, len(nums) - 1, 0
    while l < r:
        h = min(nums[l], nums[r])
        best = max(best, h * (r - l))
        if nums[l] < nums[r]:
            l += 1
        else:
            r -= 1
    return best


def longest_run(nums):
    best = cur = 1
    for i in range(1, len(nums)):
        if nums[i] > nums[i - 1]:
            cur += 1
        else:
            cur = 1
        best = max(best, cur)
    return best


def distinct_sorted(nums):
    count = 1
    for i in range(1, len(nums)):
        if nums[i] != nums[i - 1]:
            count += 1
    return count


def best_window(nums, k):
    window = sum(nums[:k])
    best = window
    for i in range(k, len(nums)):
        window += nums[i] - nums[i - k]
        best = max(best, window)
    return best


def min_rotated(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        else:
            hi = mid
    return nums[lo]


def can_jump(nums):
    reach = 0
    for i, x in enumerate(nums):
        if i > reach:
            return False
        reach = max(reach, i + x)
    return True


def profit_ii(prices):
    total = 0
    for i in range(1, len(prices)):
        if prices[i] > prices[i - 1]:
            total += prices[i] - prices[i - 1]
    return total


def is_monotonic(nums):
    up = down = True
    for i in range(1, len(nums)):
        up = up and nums[i] >= nums[i - 1]
        down = down and nums[i] <= nums[i - 1]
    return up or down


def subarray_sum(nums, k):
    seen = {0: 1}
    total = count = 0
    for i, x in enumerate(nums):
        total += x
        count += seen.get(total - k, 0)
        seen[total] = seen.get(total, 0) + 1
    return count


def second_largest(nums):
    first = second = -1
    for i, x in enumerate(nums):
        if x > first:
            first, second = x, first
        elif x > second and x != first:
            second = x
    return second


def pivot_index(nums):
    left, total = 0, sum(nums)
    for i, x in enumerate(nums):
        if left == total - left - x:
            return i
        left += x
    return -1


MORE = {
    4: dict(slug='contains-duplicate', title='Contains Duplicate', pattern='Hash set',
            prompt='Does any value appear twice?', fn=contains_duplicate, args=dict(nums=[4, 7, 1, 9, 7, 3]),
            array='nums', pointers={'i': 'i'}, show=['x', 'seen'],
            notes={'seen = set()': 'A set of values met so far.', 'for i, x in enumerate(nums):': 'Walk the array once.',
                   'if x in seen:': 'Seen this value before?', 'return True': 'Yes: a duplicate.', 'seen.add(x)': 'No: remember it.',
                   'return False': 'All values were new.'},
            complexity='O(n) time · O(n) space'),
    5: dict(slug='maximum-subarray', title='Maximum Subarray', pattern="Kadane's algorithm",
            prompt='Find the contiguous slice with the largest sum.', fn=max_subarray, args=dict(nums=[-2, 1, -3, 4, -1, 2, 1]),
            array='nums', pointers={'i': 'i'}, show=['cur', 'best'],
            notes={'cur = best = nums[0]': 'Start with the first value.', 'for i in range(1, len(nums)):': 'Extend the slice one value at a time.',
                   'cur = max(nums[i], cur + nums[i])': 'Extend, or start fresh here?', 'best = max(best, cur)': 'Keep the best slice so far.',
                   'return best': 'The largest sum.'},
            complexity='O(n) time · O(1) space'),
    6: dict(slug='missing-number', title='Missing Number', pattern='Math',
            prompt='Numbers 0 to n, one is missing. Find it.', fn=missing_number, args=dict(nums=[3, 0, 1, 5, 2]),
            array='nums', pointers={'i': 'i'}, show=['total', 'x'],
            notes={'total = len(nums) * (len(nums) + 1) // 2': 'The sum 0..n if nothing was missing.',
                   'for i, x in enumerate(nums):': 'Go through what we have.', 'total -= x': 'Take each value off the total.',
                   'return total': 'What is left is the missing number.'},
            complexity='O(n) time · O(1) space'),
    7: dict(slug='single-number', title='Single Number', pattern='XOR',
            prompt='Every value appears twice except one. Find it.', fn=single_number, args=dict(nums=[4, 1, 2, 1, 2]),
            array='nums', pointers={'i': 'i'}, show=['x', 'ans'],
            notes={'ans = 0': 'XOR with 0 changes nothing.', 'for i, x in enumerate(nums):': 'Visit every value.',
                   'ans ^= x': 'Equal pairs cancel to 0.', 'return ans': 'Only the single value is left.'},
            complexity='O(n) time · O(1) space'),
    8: dict(slug='majority-element', title='Majority Element', pattern='Boyer-Moore vote',
            prompt='Find the value that appears more than half the time.', fn=majority, args=dict(nums=[2, 2, 1, 1, 1, 2, 2]),
            array='nums', pointers={'i': 'i'}, show=['x', 'cand', 'count'],
            notes={'cand, count = nums[0], 0': 'No candidate has votes yet.', 'for i, x in enumerate(nums):': 'Let every value vote.',
                   'if count == 0:': 'Out of votes?', 'cand = x': 'Pick a new candidate.',
                   'count += 1 if x == cand else -1': 'Same value +1, different -1.', 'return cand': 'The majority survives.'},
            complexity='O(n) time · O(1) space'),
    9: dict(slug='house-robber', title='House Robber', pattern='Dynamic programming',
            prompt='Rob houses for the most money, never two neighbours.', fn=house_robber, args=dict(nums=[2, 7, 9, 3, 1]),
            array='nums', pointers={'i': 'i'}, show=['x', 'take', 'skip'],
            notes={'take, skip = 0, 0': 'Best total if we rob / skip the last house.', 'for i, x in enumerate(nums):': 'Go house by house.',
                   'take, skip = skip + x, max(take, skip)': 'Rob this one, or skip it.', 'return max(take, skip)': 'The better of the two.'},
            complexity='O(n) time · O(1) space'),
    10: dict(slug='search-insert-position', title='Search Insert Position', pattern='Binary search',
             prompt='Where would the target go in a sorted array?', fn=search_insert, args=dict(nums=[1, 3, 5, 6, 8, 10], target=7),
             array='nums', pointers={'lo': 'lo', 'mid': 'mid', 'hi': 'hi'}, show=['target', 'lo', 'mid', 'hi'],
             notes={'lo, hi = 0, len(nums) - 1': 'Search the whole array.', 'while lo <= hi:': 'Anything left to search?',
                    'mid = (lo + hi) // 2': 'Look at the middle.', 'if nums[mid] < target:': 'Is the middle too small?',
                    'lo = mid + 1': 'Go right.', 'hi = mid - 1': 'Go left.', 'return lo': 'lo is where the target belongs.'},
             complexity='O(log n) time · O(1) space'),
    11: dict(slug='find-peak-element', title='Find Peak Element', pattern='Binary search',
             prompt='Find an index bigger than both neighbours.', fn=find_peak, args=dict(nums=[1, 3, 6, 9, 7, 4, 2]),
             array='nums', pointers={'lo': 'lo', 'mid': 'mid', 'hi': 'hi'}, show=['lo', 'mid', 'hi'],
             notes={'lo, hi = 0, len(nums) - 1': 'Search the whole array.', 'while lo < hi:': 'Narrow it down.',
                    'mid = (lo + hi) // 2': 'Look at the middle.', 'if nums[mid] < nums[mid + 1]:': 'Still climbing?',
                    'lo = mid + 1': 'Peak is to the right.', 'hi = mid': 'Peak is here or to the left.', 'return lo': 'A peak.'},
             complexity='O(log n) time · O(1) space'),
    12: dict(slug='two-sum-sorted', title='Two Sum II (Sorted)', pattern='Two pointers',
             prompt='In a sorted array, find the pair that hits the target.', fn=two_sum_sorted, args=dict(nums=[1, 3, 4, 6, 8, 11], target=10),
             array='nums', pointers={'l': 'l', 'r': 'r'}, show=['target', 'total'],
             notes={'l, r = 0, len(nums) - 1': 'One pointer at each end.', 'while l < r:': 'Until they meet.',
                    'total = nums[l] + nums[r]': 'Add the two ends.', 'if total == target:': 'Hit the target?', 'return [l, r]': 'Found the pair.',
                    'if total < target:': 'Too small?', 'l += 1': 'Need bigger: move left pointer up.', 'r -= 1': 'Need smaller: move right pointer down.'},
             complexity='O(n) time · O(1) space'),
    13: dict(slug='container-with-most-water', title='Container With Most Water', pattern='Two pointers',
             prompt='Pick two bars that hold the most water.', fn=max_water, args=dict(nums=[1, 8, 6, 2, 5, 4, 8, 3]),
             array='nums', pointers={'l': 'l', 'r': 'r'}, show=['h', 'best'],
             notes={'l, r, best = 0, len(nums) - 1, 0': 'Start with the widest container.', 'while l < r:': 'Until the bars meet.',
                    'h = min(nums[l], nums[r])': 'Water rises to the shorter bar.', 'best = max(best, h * (r - l))': 'Height times width.',
                    'if nums[l] < nums[r]:': 'Which bar is shorter?', 'l += 1': 'Move the shorter one in.', 'r -= 1': 'Move the shorter one in.',
                    'return best': 'The biggest container.'},
             complexity='O(n) time · O(1) space'),
    14: dict(slug='longest-increasing-run', title='Longest Increasing Run', pattern='One pass',
             prompt='Longest stretch where every value is bigger than the last.', fn=longest_run, args=dict(nums=[3, 1, 2, 4, 5, 2, 6]),
             array='nums', pointers={'i': 'i'}, show=['cur', 'best'],
             notes={'best = cur = 1': 'One value is a run of 1.', 'for i in range(1, len(nums)):': 'Compare each value to the last.',
                    'if nums[i] > nums[i - 1]:': 'Bigger than the last?', 'cur += 1': 'Extend the run.', 'cur = 1': 'Restart the run.', 'best = max(best, cur)': 'Keep the longest.',
                    'return best': 'The longest run.'},
             complexity='O(n) time · O(1) space'),
    15: dict(slug='distinct-in-sorted', title='Count Distinct in Sorted Array', pattern='One pass',
             prompt='Count the different values in a sorted array.', fn=distinct_sorted, args=dict(nums=[1, 1, 2, 2, 2, 3, 5, 5]),
             array='nums', pointers={'i': 'i'}, show=['count'],
             notes={'count = 1': 'The first value is new.', 'for i in range(1, len(nums)):': 'Walk the array.',
                    'if nums[i] != nums[i - 1]:': 'Different from the previous?', 'count += 1': 'A new value.', 'return count': 'Distinct values.'},
             complexity='O(n) time · O(1) space'),
    16: dict(slug='max-sum-window', title='Maximum Sum of Size K', pattern='Sliding window',
             prompt='Best sum of any k values in a row.', fn=best_window, args=dict(nums=[2, 1, 5, 1, 3, 2, 4], k=3),
             array='nums', pointers={'i': 'i'}, show=['k', 'window', 'best'],
             notes={'window = sum(nums[:k])': 'Sum of the first window.', 'best = window': 'That is the best so far.',
                    'for i in range(k, len(nums)):': 'Slide one step at a time.', 'window += nums[i] - nums[i - k]': 'Add the new value, drop the old.',
                    'best = max(best, window)': 'Keep the best window.', 'return best': 'The best sum.'},
             complexity='O(n) time · O(1) space'),
    17: dict(slug='min-in-rotated', title='Minimum in Rotated Array', pattern='Binary search',
             prompt='A sorted array was rotated. Find the smallest value.', fn=min_rotated, args=dict(nums=[6, 7, 9, 1, 2, 3, 4]),
             array='nums', pointers={'lo': 'lo', 'mid': 'mid', 'hi': 'hi'}, show=['lo', 'mid', 'hi'],
             notes={'lo, hi = 0, len(nums) - 1': 'Search the whole array.', 'while lo < hi:': 'Narrow it down.',
                    'mid = (lo + hi) // 2': 'Look at the middle.', 'if nums[mid] > nums[hi]:': 'Middle bigger than the end?',
                    'lo = mid + 1': 'The smallest is to the right.', 'hi = mid': 'The smallest is here or left.', 'return nums[lo]': 'The smallest value.'},
             complexity='O(log n) time · O(1) space'),
    18: dict(slug='jump-game', title='Jump Game', pattern='Greedy',
             prompt='Each value is your max jump. Can you reach the end?', fn=can_jump, args=dict(nums=[2, 3, 1, 1, 4]),
             array='nums', pointers={'i': 'i'}, show=['x', 'reach'],
             notes={'reach = 0': 'Furthest index reachable so far.', 'for i, x in enumerate(nums):': 'Visit each index.',
                    'if i > reach:': 'Is this index out of reach?', 'return False': 'Stuck: cannot get here.',
                    'reach = max(reach, i + x)': 'Jump as far as possible.', 'return True': 'Every index was reachable.'},
             complexity='O(n) time · O(1) space'),
    19: dict(slug='stock-profit-ii', title='Best Time to Buy and Sell Stock II', pattern='Greedy',
             prompt='Trade as often as you like. Maximise the profit.', fn=profit_ii, args=dict(prices=[7, 1, 5, 3, 6, 4]),
             array='prices', pointers={'i': 'i'}, show=['total'],
             notes={'total = 0': 'No profit yet.', 'for i in range(1, len(prices)):': 'Compare each day with the last.',
                    'if prices[i] > prices[i - 1]:': 'Price went up?', 'total += prices[i] - prices[i - 1]': 'Bank every rise.',
                    'return total': 'Total profit.'},
             complexity='O(n) time · O(1) space'),
    20: dict(slug='monotonic-array', title='Monotonic Array', pattern='One pass',
             prompt='Is the array only going up, or only going down?', fn=is_monotonic, args=dict(nums=[6, 5, 5, 3, 1, 1]),
             array='nums', pointers={'i': 'i'}, show=['up', 'down'],
             notes={'up = down = True': 'Assume both are possible.', 'for i in range(1, len(nums)):': 'Compare neighbours.',
                    'up = up and nums[i] >= nums[i - 1]': 'A drop breaks "up".', 'down = down and nums[i] <= nums[i - 1]': 'A rise breaks "down".',
                    'return up or down': 'Either one survived?'},
             complexity='O(n) time · O(1) space'),
    21: dict(slug='subarray-sum-k', title='Subarray Sum Equals K', pattern='Prefix sums + hash map',
             prompt='Count the slices whose sum is exactly k.', fn=subarray_sum, args=dict(nums=[1, 2, 3, 1, 2], k=3),
             array='nums', pointers={'i': 'i'}, show=['k', 'total', 'count'],
             notes={'seen = {0: 1}': 'How often each prefix sum occurred.', 'total = count = 0': 'Running sum and answer.',
                    'for i, x in enumerate(nums):': 'Walk the array.', 'total += x': 'Extend the running sum.',
                    'count += seen.get(total - k, 0)': 'Earlier prefixes that leave a slice of k.',
                    'seen[total] = seen.get(total, 0) + 1': 'Remember this prefix sum.', 'return count': 'Slices with sum k.'},
             complexity='O(n) time · O(n) space'),
    22: dict(slug='second-largest', title='Second Largest Value', pattern='One pass',
             prompt='Find the second biggest distinct value.', fn=second_largest, args=dict(nums=[5, 9, 2, 9, 7, 3]),
             array='nums', pointers={'i': 'i'}, show=['x', 'first', 'second'],
             notes={'first = second = -1': 'Nothing found yet.', 'for i, x in enumerate(nums):': 'Visit every value.',
                    'if x > first:': 'New biggest?', 'first, second = x, first': 'Old biggest becomes second.',
                    'elif x > second and x != first:': 'Between the two?', 'second = x': 'New second place.', 'return second': 'Second largest.'},
             complexity='O(n) time · O(1) space'),
    23: dict(slug='pivot-index', title='Find Pivot Index', pattern='Prefix sums',
             prompt='Find the index where left sum equals right sum.', fn=pivot_index, args=dict(nums=[1, 7, 3, 6, 5, 6]),
             array='nums', pointers={'i': 'i'}, show=['x', 'left', 'total'],
             notes={'left, total = 0, sum(nums)': 'Left sum is 0, total is known.', 'for i, x in enumerate(nums):': 'Try each index.',
                    'if left == total - left - x:': 'Left equals right?', 'return i': 'Found the pivot.', 'left += x': 'Grow the left sum.',
                    'return -1': 'No pivot.'},
             complexity='O(n) time · O(1) space'),
}
