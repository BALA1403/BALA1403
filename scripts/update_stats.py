# scripts/update_stats.py - Daily Progress Tracker
import requests
import json
import os
from datetime import datetime, timezone
import re
from bs4 import BeautifulSoup
import time

def fetch_leetcode_stats(username="bxlz14"):
    """Fetch LeetCode daily progress"""
    print(f"🔥 Fetching LeetCode progress for {username}...")
    
    query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            username
            profile {
                ranking
                reputation
            }
            submitStats {
                acSubmissionNum {
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
                
                stats = {
                    'platform': 'LeetCode',
                    'username': user_data['username'],
                    'ranking': user_data['profile'].get('ranking', 'N/A'),
                    'solved_problems': {
                        'easy': 0,
                        'medium': 0,
                        'hard': 0,
                        'total': 0
                    },
                    'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
                    'daily_update': True
                }
                
                # Parse submission stats
                for submission in user_data['submitStats']['acSubmissionNum']:
                    difficulty = submission['difficulty'].lower()
                    if difficulty in ['easy', 'medium', 'hard']:
                        stats['solved_problems'][difficulty] = submission['count']
                    elif difficulty == 'all':
                        stats['solved_problems']['total'] = submission['count']
                
                # Save daily progress
                os.makedirs('data', exist_ok=True)
                with open('data/leetcode_stats.json', 'w') as f:
                    json.dump(stats, f, indent=2)
                    
                total = stats['solved_problems']['total']
                ranking = f"#{stats['ranking']}" if stats['ranking'] != 'N/A' else 'Unranked'
                print(f"✅ LeetCode: {total} problems solved, Rank: {ranking}")
                return stats
            else:
                print("❌ LeetCode: No user data found")
                return None
                
    except Exception as e:
        print(f"❌ LeetCode error: {e}")
        return None

def fetch_geeksforgeeks_stats(username="bxlz14"):
    """Fetch GeeksforGeeks daily progress"""
    print(f"🚀 Fetching GeeksforGeeks progress for {username}...")
    
    try:
        url = f"https://auth.geeksforgeeks.org/user/{username}/practice/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            stats = {
                'platform': 'GeeksforGeeks',
                'username': username,
                'problems_solved': 0,
                'coding_score': 0,
                'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
                'daily_update': True
            }
            
            # Enhanced selectors for problem count
            selectors = [
                '.score_card_value',
                '.scoreCard_head_left--score__oSi_x',
                '.problemsSolved--count',
                '.problems-solved',
                '.solvedProblemCount',
                '.profile-stat-value'
            ]
            
            problems_solved = 0
            
            # Try to find problems solved count
            for selector in selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text().strip()
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        try:
                            num = int(numbers[0])
                            if 0 < num < 10000:  # Reasonable range
                                problems_solved = max(problems_solved, num)
                        except ValueError:
                            continue
            
            # Check script tags for embedded data
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and 'problemsSolved' in script.string:
                    matches = re.findall(r'"problemsSolved"\s*:\s*(\d+)', script.string)
                    if matches:
                        try:
                            problems_solved = max(problems_solved, int(matches[0]))
                        except ValueError:
                            continue
            
            stats['problems_solved'] = problems_solved
            
            # Save daily progress
            os.makedirs('data', exist_ok=True)
            with open('data/geeksforgeeks_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
            
            print(f"✅ GeeksforGeeks: {stats['problems_solved']} problems solved")
            return stats
            
    except Exception as e:
        print(f"❌ GeeksforGeeks error: {e}")
        # Return default to prevent crashes
        return {
            'platform': 'GeeksforGeeks',
            'username': username,
            'problems_solved': 0,
            'coding_score': 0,
            'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
            'daily_update': True
        }

def fetch_hackerrank_stats(username="bxlz_14"):
    """Fetch HackerRank daily progress"""
    print(f"⭐ Fetching HackerRank progress for {username}...")
    
    try:
        url = f"https://www.hackerrank.com/profile/{username}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        stats = {
            'platform': 'HackerRank',
            'username': username,
            'badges': 0,
            'gold_badges': 0,
            'silver_badges': 0,
            'bronze_badges': 0,
            'problems_solved': 0,
            'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
            'daily_update': True
        }
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Count badges
            badge_elements = soup.find_all(['div', 'span'], class_=re.compile(r'badge', re.I))
            stats['badges'] = len([elem for elem in badge_elements if elem.get_text().strip()])
            
            # Look for problems solved
            problem_elements = soup.find_all(text=re.compile(r'\d+.*(?:problem|challenge).*solved', re.I))
            for elem in problem_elements:
                numbers = re.findall(r'\d+', elem)
                if numbers:
                    stats['problems_solved'] = int(numbers[0])
                    break
        
        # Save daily progress
        os.makedirs('data', exist_ok=True)
        with open('data/hackerrank_stats.json', 'w') as f:
            json.dump(stats, f, indent=2)
            
        print(f"✅ HackerRank: {stats['badges']} badges, {stats['problems_solved']} problems")
        return stats
        
    except Exception as e:
        print(f"❌ HackerRank error: {e}")
        return {
            'platform': 'HackerRank',
            'username': username,
            'badges': 0,
            'problems_solved': 0,
            'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
            'daily_update': True
        }

def update_readme_with_daily_stats():
    """Update README with daily progress stats"""
    print("📝 Updating README with daily progress...")
    
    # Load all platform stats
    stats = {}
    
    for platform in ['leetcode', 'geeksforgeeks', 'hackerrank']:
        try:
            with open(f'data/{platform}_stats.json', 'r') as f:
                stats[platform] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            stats[platform] = None
    
    # Read current README
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except FileNotFoundError:
        print("❌ README.md not found")
        return
    
    # Generate daily stats section
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    
    stats_section = f"""## 📈 Daily Coding Progress (Last Updated: {current_time})

<div align="center">

### 🎯 Current Stats Overview

| 🏅 Platform | 📊 Progress | 🎖️ Achievements | 🔗 Profile |
|-------------|-------------|-----------------|------------|"""

    # LeetCode row
    if stats['leetcode'] and stats['leetcode']['solved_problems']['total'] > 0:
        lc = stats['leetcode']
        ranking = f"#{lc.get('ranking', 'N/A'):,}" if lc.get('ranking') != 'N/A' else 'Unranked'
        stats_section += f"""
| **🔥 LeetCode** | **{lc['solved_problems']['total']} Problems**<br/>Easy: {lc['solved_problems']['easy']} • Medium: {lc['solved_problems']['medium']} • Hard: {lc['solved_problems']['hard']}<br/>📈 Rank: {ranking} | 🏆 Consistent Solver<br/>⚡ Medium Progress | [Visit Profile](https://leetcode.com/bxlz14) |"""
    else:
        stats_section += """
| **🔥 LeetCode** | **Loading...** 🔄<br/>Fetching latest progress | 🔄 Updating<br/>⏳ Please wait | [Visit Profile](https://leetcode.com/bxlz14) |"""
    
    # GeeksforGeeks row
    if stats['geeksforgeeks'] and stats['geeksforgeeks']['problems_solved'] > 0:
        gfg = stats['geeksforgeeks']
        stats_section += f"""
| **🚀 GeeksforGeeks** | **{gfg['problems_solved']} Problems**<br/>Coding Score: {gfg.get('coding_score', 0)}<br/>🎯 Skill Building | 🌟 Regular Practice<br/>📚 Foundation Strong | [Visit Profile](https://auth.geeksforgeeks.org/user/bxlz14) |"""
    else:
        stats_section += """
| **🚀 GeeksforGeeks** | **Loading...** 🔄<br/>Fetching latest progress | 🔄 Updating<br/>⏳ Please wait | [Visit Profile](https://auth.geeksforgeeks.org/user/bxlz14) |"""
    
    # HackerRank row
    if stats['hackerrank']:
        hr = stats['hackerrank']
        problems_text = f" • {hr['problems_solved']} Problems" if hr['problems_solved'] > 0 else ""
        stats_section += f"""
| **⭐ HackerRank** | **{hr['badges']} Badges{problems_text}**<br/>🥇 Gold: {hr['gold_badges']} • 🥈 Silver: {hr['silver_badges']} • 🥉 Bronze: {hr['bronze_badges']} | 🏅 Badge Collector<br/>🎪 Multi-Domain | [Visit Profile](https://www.hackerrank.com/bxlz_14) |"""
    else:
        stats_section += """
| **⭐ HackerRank** | **Loading...** 🔄<br/>Fetching latest progress | 🔄 Updating<br/>⏳ Please wait | [Visit Profile](https://www.hackerrank.com/bxlz_14) |"""
    
    # Add Codolio tracker
    stats_section += """
| **📊 Codolio** | **Multi-Platform Tracker**<br/>Unified Dashboard | 🔄 Progress Sync<br/>📋 Analytics Hub | [Visit Profile](https://codolio.com/profile/bxlz.14) |

</div>

### 🚀 Today's Highlights

<div align="center">

```
🎯 Total Problems Solved: {total_problems}+
📈 Daily Goal: Consistent Practice  
🔥 Current Streak: Building Strong
⏰ Auto-Updated: Every Day at 10 PM UTC
```

</div>

### 📊 Quick Stats

<div align="center">
  <table>
    <tr>
      <td align="center">
        <img src="https://img.shields.io/badge/Total_Problems-{total_problems}+-brightgreen?style=for-the-badge&logo=target&logoColor=white"/>
      </td>
      <td align="center">
        <img src="https://img.shields.io/badge/Active_Platforms-4-blue?style=for-the-badge&logo=code&logoColor=white"/>
      </td>
      <td align="center">
        <img src="https://img.shields.io/badge/Daily_Updates-10_PM_UTC-orange?style=for-the-badge&logo=clock&logoColor=white"/>
      </td>
    </tr>
  </table>
</div>"""

    # Calculate total problems
    total_problems = 0
    if stats['leetcode']:
        total_problems += stats['leetcode']['solved_problems']['total']
    if stats['geeksforgeeks']:
        total_problems += stats['geeksforgeeks']['problems_solved']
    if stats['hackerrank']:
        total_problems += stats['hackerrank'].get('problems_solved', 0)

    # Format the stats section with calculated total
    stats_section = stats_section.format(total_problems=total_problems)
    
    # Replace the daily progress section in README
    pattern = r'## 📈 Daily Coding Progress.*?</div>'
    
    if re.search(pattern, readme_content, re.DOTALL):
        readme_content = re.sub(pattern, stats_section.strip(), readme_content, flags=re.DOTALL)
    else:
        # If section doesn't exist, add it after competitive programming
        platform_pattern = r'(### 🌐 Platform Links.*?</div>)'
        if re.search(platform_pattern, readme_content, re.DOTALL):
            readme_content = re.sub(
                platform_pattern,
                r'\1\n\n---\n\n' + stats_section,
                readme_content,
                flags=re.DOTALL
            )
    
    # Write updated README
    try:
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("✅ README updated with daily progress!")
        return True
    except Exception as e:
        print(f"❌ Error updating README: {e}")
        return False

def generate_daily_summary(stats):
    """Generate a summary of daily progress"""
    print("\n" + "="*60)
    print("📊 DAILY CODING PROGRESS SUMMARY")
    print("="*60)
    
    total_problems = 0
    platforms_updated = 0
    
    for platform, data in stats.items():
        if data and data.get('daily_update'):
            platforms_updated += 1
            if platform == 'leetcode':
                problems = data['solved_problems']['total']
                print(f"🔥 LeetCode: {problems} problems (Easy: {data['solved_problems']['easy']}, Medium: {data['solved_problems']['medium']}, Hard: {data['solved_problems']['hard']})")
                total_problems += problems
            elif platform == 'geeksforgeeks':
                problems = data['problems_solved']
                print(f"🚀 GeeksforGeeks: {problems} problems solved")
                total_problems += problems
            elif platform == 'hackerrank':
                badges = data['badges']
                problems = data.get('problems_solved', 0)
                print(f"⭐ HackerRank: {badges} badges, {problems} problems")
                total_problems += problems
    
    print("-" * 60)
    print(f"🎯 Total Problems Across Platforms: {total_problems}")
    print(f"📈 Platforms Successfully Updated: {platforms_updated}/3")
    print(f"🕙 Daily Update Completed: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("⏰ Next Update: Tomorrow at 10 PM UTC")
    print("="*60)

def main():
    """Main function for daily stats update"""
    print("🌙 Starting Daily Coding Progress Update")
    print("="*60)
    
    stats_results = {}
    success_count = 0
    
    # Fetch from all platforms
    platforms = [
        ('leetcode', fetch_leetcode_stats),
        ('geeksforgeeks', fetch_geeksforgeeks_stats),
        ('hackerrank', fetch_hackerrank_stats)
    ]
    
    for platform_name, fetch_function in platforms:
        try:
            print(f"\n📡 Connecting to {platform_name.title()}...")
            result = fetch_function()
            stats_results[platform_name] = result
            if result and result.get('daily_update'):
                success_count += 1
                print(f"✅ {platform_name.title()} updated successfully")
            else:
                print(f"⚠️ {platform_name.title()} update incomplete")
        except Exception as e:
            print(f"❌ {platform_name.title()} failed: {e}")
            stats_results[platform_name] = None
    
    # Update README with daily progress
    print(f"\n📝 Updating README with fresh data...")
    readme_updated = update_readme_with_daily_stats()
    
    # Generate summary
    generate_daily_summary(stats_results)
    
    if readme_updated:
        print("🎉 Daily update completed successfully!")
    else:
        print("⚠️ Daily update completed with some issues")
    
    return success_count, len(platforms)

if __name__ == "__main__":
    success, total = main()