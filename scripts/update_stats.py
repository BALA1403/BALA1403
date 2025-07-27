# scripts/update_stats.py
import requests
import json
import os
from datetime import datetime
import re
from bs4 import BeautifulSoup
import time

def fetch_leetcode_stats(username="bxlz14"):
    """Fetch LeetCode user statistics"""
    print(f"Fetching LeetCode stats for {username}...")
    
    # GraphQL query for LeetCode API
    query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            username
            profile {
                ranking
                userAvatar
                realName
                aboutMe
                reputation
            }
            submitStats {
                acSubmissionNum {
                    difficulty
                    count
                    submissions
                }
                totalSubmissionNum {
                    difficulty
                    count
                    submissions
                }
            }
        }
    }
    """
    
    url = "https://leetcode.com/graphql"
    variables = {"username": username}
    
    try:
        response = requests.post(
            url,
            json={"query": query, "variables": variables},
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['matchedUser']:
                user_data = data['data']['matchedUser']
                
                # Extract key statistics
                stats = {
                    'username': user_data['username'],
                    'ranking': user_data['profile'].get('ranking', 'N/A'),
                    'reputation': user_data['profile'].get('reputation', 0),
                    'solved_problems': {
                        'easy': 0,
                        'medium': 0,
                        'hard': 0,
                        'total': 0
                    },
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
                }
                
                # Parse submission stats
                for submission in user_data['submitStats']['acSubmissionNum']:
                    difficulty = submission['difficulty'].lower()
                    if difficulty in ['easy', 'medium', 'hard']:
                        stats['solved_problems'][difficulty] = submission['count']
                    elif difficulty == 'all':
                        stats['solved_problems']['total'] = submission['count']
                
                # Save to file
                os.makedirs('data', exist_ok=True)
                with open('data/leetcode_stats.json', 'w') as f:
                    json.dump(stats, f, indent=2)
                    
                print(f"✅ LeetCode stats updated: {stats['solved_problems']['total']} problems solved")
                return stats
            else:
                print("❌ No LeetCode data found for user")
                return None
                
    except Exception as e:
        print(f"❌ Error fetching LeetCode stats: {e}")
        return None

def fetch_geeksforgeeks_stats(username="bxlz14"):
    """Fetch GeeksforGeeks user statistics with improved scraping"""
    print(f"Fetching GeeksforGeeks stats for {username}...")
    
    try:
        url = f"https://auth.geeksforgeeks.org/user/{username}/practice/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        print(f"GeeksforGeeks response status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            stats = {
                'username': username,
                'problems_solved': 0,
                'coding_score': 0,
                'institute_rank': 'N/A',
                'easy_solved': 0,
                'medium_solved': 0,
                'hard_solved': 0,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            }
            
            # Enhanced selectors for GeeksforGeeks
            selectors_to_try = [
                '.score_card_value',
                '.scoreCard_head_left--score__oSi_x',
                '.problemsSolved--count',
                '.problems-solved',
                '.solvedProblemCount',
                '.user-profile-stats .stat-value',
                '.stat-number',
                '[data-problems-solved]',
                '.profile-stat-value'
            ]
            
            problems_solved = 0
            
            # Try each selector
            for selector in selectors_to_try:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text().strip()
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        try:
                            num = int(numbers[0])
                            if num > problems_solved and num < 10000:  # Reasonable upper limit
                                problems_solved = num
                        except ValueError:
                            continue
            
            # Alternative: Look for API endpoints or embedded JSON
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and ('problemsSolved' in script.string or 'problems_solved' in script.string):
                    # Extract from JSON-like structures
                    json_matches = re.findall(r'"(?:problemsSolved|problems_solved)"\s*:\s*(\d+)', script.string)
                    if json_matches:
                        try:
                            problems_solved = max(problems_solved, int(json_matches[0]))
                        except ValueError:
                            continue
            
            stats['problems_solved'] = problems_solved
            
            # Try to extract difficulty-wise stats
            difficulty_patterns = {
                'easy': [r'easy[:\s]*(\d+)', r'beginner[:\s]*(\d+)', r'school[:\s]*(\d+)'],
                'medium': [r'medium[:\s]*(\d+)', r'basic[:\s]*(\d+)'],
                'hard': [r'hard[:\s]*(\d+)', r'difficult[:\s]*(\d+)']
            }
            
            page_text = soup.get_text().lower()
            for difficulty, patterns in difficulty_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        try:
                            stats[f'{difficulty}_solved'] = int(matches[0])
                            break
                        except ValueError:
                            continue
            
            # Save to file
            os.makedirs('data', exist_ok=True)
            with open('data/geeksforgeeks_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
            
            print(f"✅ GeeksforGeeks stats updated: {stats['problems_solved']} problems solved")
            return stats
            
    except Exception as e:
        print(f"❌ Error fetching GeeksforGeeks stats: {e}")
        # Return default stats to prevent crashes
        return {
            'username': username,
            'problems_solved': 0,
            'coding_score': 0,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        }

def fetch_hackerrank_stats(username="bxlz_14"):
    """Fetch HackerRank user statistics"""
    print(f"Fetching HackerRank stats for {username}...")
    
    try:
        # Try profile page scraping
        url = f"https://www.hackerrank.com/profile/{username}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            stats = {
                'username': username,
                'badges': 0,
                'gold_badges': 0,
                'silver_badges': 0,
                'bronze_badges': 0,
                'problems_solved': 0,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            }
            
            # Try to find badge information
            badge_elements = soup.find_all(['div', 'span'], class_=re.compile(r'badge', re.I))
            stats['badges'] = len([elem for elem in badge_elements if elem.get_text().strip()])
            
            # Look for solved problems count
            problem_elements = soup.find_all(text=re.compile(r'\d+.*(?:problem|challenge).*solved', re.I))
            for elem in problem_elements:
                numbers = re.findall(r'\d+', elem)
                if numbers:
                    stats['problems_solved'] = int(numbers[0])
                    break
            
            # Save to file
            os.makedirs('data', exist_ok=True)
            with open('data/hackerrank_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
                
            print(f"✅ HackerRank stats updated: {stats['badges']} badges, {stats['problems_solved']} problems")
            return stats
            
    except Exception as e:
        print(f"❌ Error fetching HackerRank stats: {e}")
        
    # Return default stats
    return {
        'username': username,
        'badges': 0,
        'gold_badges': 0,
        'silver_badges': 0,
        'bronze_badges': 0,
        'problems_solved': 0,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    }

def generate_readme_with_stats():
    """Generate README with updated stats and improved formatting (TUF removed)"""
    print("Generating updated README...")
    
    # Load all stats with error handling
    stats = {}
    
    # Load LeetCode stats
    try:
        with open('data/leetcode_stats.json', 'r') as f:
            stats['leetcode'] = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        stats['leetcode'] = None
    
    # Load GeeksforGeeks stats
    try:
        with open('data/geeksforgeeks_stats.json', 'r') as f:
            stats['geeksforgeeks'] = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        stats['geeksforgeeks'] = None
    
    # Load HackerRank stats
    try:
        with open('data/hackerrank_stats.json', 'r') as f:
            stats['hackerrank'] = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        stats['hackerrank'] = None
    
    # Read current README
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except FileNotFoundError:
        print("❌ README.md not found")
        return
    
    # Create enhanced stats section
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    stats_section = f"""## 📊 Current Coding Stats (Updated: {current_time})

<div align="center">
  
| Platform | Stats | Profile |
|----------|--------|---------|"""

    # LeetCode stats
    if stats['leetcode'] and stats['leetcode']['solved_problems']['total'] > 0:
        lc = stats['leetcode']
        ranking_text = f"#{lc.get('ranking', 'N/A')}" if lc.get('ranking') != 'N/A' else 'Unranked'
        stats_section += f"""
| 🔥 **LeetCode** | **{lc['solved_problems']['total']}** problems solved<br/>Easy: {lc['solved_problems']['easy']} \\| Medium: {lc['solved_problems']['medium']} \\| Hard: {lc['solved_problems']['hard']}<br/>Ranking: {ranking_text} | [bxlz14](https://leetcode.com/bxlz14) |"""
    else:
        stats_section += """
| 🔥 **LeetCode** | **Loading...** 🔄<br/>Fetching latest stats | [bxlz14](https://leetcode.com/bxlz14) |"""
    
    # GeeksforGeeks stats
    if stats['geeksforgeeks'] and stats['geeksforgeeks']['problems_solved'] > 0:
        gfg = stats['geeksforgeeks']
        breakdown = ""
        if gfg.get('easy_solved', 0) + gfg.get('medium_solved', 0) + gfg.get('hard_solved', 0) > 0:
            breakdown = f"<br/>Easy: {gfg.get('easy_solved', 0)} \\| Medium: {gfg.get('medium_solved', 0)} \\| Hard: {gfg.get('hard_solved', 0)}"
        
        stats_section += f"""
| 🚀 **GeeksforGeeks** | **{gfg['problems_solved']}** problems solved{breakdown}<br/>Coding Score: {gfg.get('coding_score', 0)} | [bxlz14](https://auth.geeksforgeeks.org/user/bxlz14) |"""
    else:
        stats_section += """
| 🚀 **GeeksforGeeks** | **Loading...** 🔄<br/>Fetching latest stats | [bxlz14](https://auth.geeksforgeeks.org/user/bxlz14) |"""
    
    # HackerRank stats
    if stats['hackerrank']:
        hr = stats['hackerrank']
        problems_text = f" \\| {hr['problems_solved']} problems" if hr['problems_solved'] > 0 else ""
        stats_section += f"""
| ⭐ **HackerRank** | **{hr['badges']}** badges earned{problems_text}<br/>🥇 {hr['gold_badges']} \\| 🥈 {hr['silver_badges']} \\| 🥉 {hr['bronze_badges']} | [bxlz_14](https://www.hackerrank.com/bxlz_14) |"""
    else:
        stats_section += """
| ⭐ **HackerRank** | **Loading...** 🔄<br/>Fetching latest stats | [bxlz_14](https://www.hackerrank.com/bxlz_14) |"""
    
    # Add multi-platform tracker
    stats_section += """
| 🔗 **Codolio** | Multi-platform Progress Tracker<br/>Unified coding stats dashboard | [bxlz.14](https://codolio.com/profile/bxlz.14) |

</div>

### 📈 Progress Summary
<div align="center">
"""

    # Calculate total problems across platforms (excluding TUF)
    total_problems = 0
    if stats['leetcode']:
        total_problems += stats['leetcode']['solved_problems']['total']
    if stats['geeksforgeeks']:
        total_problems += stats['geeksforgeeks']['problems_solved']
    if stats['hackerrank']:
        total_problems += stats['hackerrank'].get('problems_solved', 0)

    stats_section += f"""
**Total Problems Solved: {total_problems}+ 🎯**

*Last Updated: {current_time} | Auto-updated daily via GitHub Actions ⚡*

</div>"""
    
    # Find and replace the stats section in README
    pattern = r'## 📊 Current Coding Stats.*?</div>'
    
    if re.search(pattern, readme_content, re.DOTALL):
        readme_content = re.sub(pattern, stats_section.strip(), readme_content, flags=re.DOTALL)
    else:
        # If stats section doesn't exist, add it after competitive programming
        competitive_pattern = r'(### Codolio Profile.*?</div>)'
        if re.search(competitive_pattern, readme_content, re.DOTALL):
            readme_content = re.sub(
                competitive_pattern, 
                r'\1\n\n' + stats_section, 
                readme_content, 
                flags=re.DOTALL
            )
        else:
            # Add before connect section
            connect_pattern = r'(## 🤝 Connect with Me)'
            if re.search(connect_pattern, readme_content):
                readme_content = re.sub(
                    connect_pattern,
                    stats_section + '\n\n' + r'\1',
                    readme_content
                )
    
    # Write updated README
    try:
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("✅ README.md updated with stats (TUF removed)!")
    except Exception as e:
        print(f"❌ Error writing README: {e}")

def main():
    """Main function to update all stats (TUF removed)"""
    print("🚀 Starting stats update process (TUF removed)...")
    print("=" * 60)
    
    success_count = 0
    total_platforms = 3  # Reduced from 4 to 3
    
    # Fetch stats from platforms (TUF removed)
    try:
        lc_stats = fetch_leetcode_stats()
        if lc_stats:
            success_count += 1
    except Exception as e:
        print(f"❌ LeetCode fetch failed: {e}")
    
    try:
        gfg_stats = fetch_geeksforgeeks_stats()
        if gfg_stats and gfg_stats['problems_solved'] > 0:
            success_count += 1
    except Exception as e:
        print(f"❌ GeeksforGeeks fetch failed: {e}")
    
    try:
        hr_stats = fetch_hackerrank_stats()
        if hr_stats:
            success_count += 1
    except Exception as e:
        print(f"❌ HackerRank fetch failed: {e}")
    
    # Update README
    try:
        generate_readme_with_stats()
        print(f"✅ README updated successfully!")
    except Exception as e:
        print(f"❌ README update failed: {e}")
    
    print("=" * 60)
    print(f"📊 Stats update completed: {success_count}/{total_platforms} platforms successful")
    print(f"🕒 Process completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("✅ TakeUForward (TUF) stats have been removed from the automation")

if __name__ == "__main__":
    main()
