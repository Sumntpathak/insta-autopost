"""DSA series: one entry per episode. The code shown in the video IS this code, and every
highlighted line and variable value comes from actually running it (sys.settrace), so the
debugger view can never drift from the real behaviour.

Add an episode: write the solution function (short, no blank lines inside, at most ~10 lines),
then add a spec to PROBLEMS. Problem statements are written in our own words.
Fields:
  title, pattern, prompt  - text on screen
  fn, args                - the function and the example input it runs on
  array                   - name of the list argument drawn as cells
  pointers                - {variable name: label} drawn as arrows under the array (indices)
  show                    - variables listed in the watch panel, in order
  notes                   - {exact line text: narration shown while that line runs}
  complexity              - shown at the end
"""


def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        need = target - x
        if need in seen:
            return [seen[need], i]
        seen[x] = i
    return []


def max_profit(prices):
    best = 0
    low = prices[0]
    for i in range(1, len(prices)):
        low = min(low, prices[i])
        best = max(best, prices[i] - low)
    return best


def binary_search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


PROBLEMS = {
    1: dict(slug='two-sum', title='Two Sum', pattern='Hash map',
            prompt='Find two numbers that add up to the target.',
            fn=two_sum, args=dict(nums=[3, 8, 4, 6, 1], target=10),
            array='nums', pointers={'i': 'i'}, show=['target', 'x', 'need', 'seen'],
            notes={'seen = {}': 'A map from value to its index.',
                   'for i, x in enumerate(nums):': 'Walk the array once.',
                   'need = target - x': 'Which number would complete the pair?',
                   'if need in seen:': 'Have we already seen it?',
                   'return [seen[need], i]': 'Yes: the pair is found.',
                   'seen[x] = i': 'No: remember x and its index.'},
            complexity='O(n) time · O(n) space'),
    2: dict(slug='best-time-to-buy-and-sell-stock', title='Best Time to Buy and Sell Stock', pattern='One pass',
            prompt='Buy on one day, sell on a later day. Maximise the profit.',
            fn=max_profit, args=dict(prices=[7, 1, 5, 3, 6, 4]),
            array='prices', pointers={'i': 'i'}, show=['low', 'best'],
            notes={'best = 0': 'No trade yet: profit 0.',
                   'low = prices[0]': 'Cheapest price so far.',
                   'for i in range(1, len(prices)):': 'Check every later day.',
                   'low = min(low, prices[i])': 'Is today the cheapest buy?',
                   'best = max(best, prices[i] - low)': 'Would selling today beat the best?',
                   'return best': 'Best profit found.'},
            complexity='O(n) time · O(1) space'),
    3: dict(slug='binary-search', title='Binary Search', pattern='Two pointers',
            prompt='Find the target in a sorted array, halving the search each step.',
            fn=binary_search, args=dict(nums=[1, 3, 5, 7, 9, 11, 13], target=11),
            array='nums', pointers={'lo': 'lo', 'mid': 'mid', 'hi': 'hi'}, show=['target', 'lo', 'mid', 'hi'],
            notes={'lo, hi = 0, len(nums) - 1': 'Search the whole array.',
                   'while lo <= hi:': 'Anything left to search?',
                   'mid = (lo + hi) // 2': 'Look at the middle.',
                   'if nums[mid] == target:': 'Is it the target?',
                   'return mid': 'Found it.',
                   'if nums[mid] < target:': 'Too small? Go right.',
                   'lo = mid + 1': 'Drop the left half.',
                   'hi = mid - 1': 'Drop the right half.'},
            complexity='O(log n) time · O(1) space'),
}
