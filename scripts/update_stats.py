# scripts/update_daily_stats.py
import requests
import json
import os
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
import time
from dateutil import tz

def get_local_time():
    """Get current time in IST (Indian Standard Time)"""
    utc = tz.gettz('UTC')
    ist = tz.gettz('Asia/Kolkata')
    utc_time = datetime.now(utc)
    ist_time = utc_time.astimezone(ist)
    return ist_time

def fetch_leetcode_stats(username="bxlz14"):
    """Fetch LeetCode user statistics with enhanced error handling"""
    print(f"🔥 Fetching LeetCode stats for {username}...")
    
    query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            username
            profile {
                ranking
                userAvatar
                realName
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
            recentSubmissionList(limit: 10) {
                title
                statusDisplay
                timestamp
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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://leetcode.com/",
            },
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['matchedUser']:
                user_data = data['data']['matchedUser']
                
                current_time = get_local_time()
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
                    'recent_activity': [],
                    'last_updated': current_time.strftime('%Y-%m-%d %H:%M:%S IST'),
                    'last_updated_utc': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
                }
                
                # Parse submission stats
                for submission in user_data['submitStats']['acSubmissionNum']:
                    difficulty = submission['difficulty'].lower()
                    if difficulty in ['easy', 'medium', 'hard']:
                        stats['solved_problems'][difficulty] = submission['count']
                    elif difficulty == 'all':
                        stats['solved_problems']['total'] = submission['count']
                
                # Parse recent submissions
                if user_data.get('recentSubmissionList'):
                    for submission in user_data['recentSubmissionList'][:5]:
                        if submission['statusDisplay'] == 'Accepted':
                            stats['recent_activity'].append({
                                'title': submission['title'],
                                'status': submission['statusDisplay'],
                                'timestamp': submission['timestamp']
                            })
                
                # Save to platform stats
                os.makedirs('data/platform_stats', exist_ok=True)
                with open('data/platform_stats/leetcode_stats.json', 'w') as f:
                    json.dump(stats, f, indent=2)
                    
                print(f"✅ LeetCode: {stats['solved_problems']['total']} total problems (Easy: {stats['solved_problems']['easy']}, Medium: {stats['solved_problems']['medium']}, Hard: {stats['solved_problems']['hard']})")
                return stats
            else:
                print("❌ No LeetCode data found for user")
                return None
                
    except Exception as e:
        print(f"❌ Error fetching LeetCode stats: {e}")
        return None

def fetch_geeksforgeeks_stats(username="bxlz14"):
    """Fetch GeeksforGeeks user statistics with enhanced scraping"""
    print(f"🚀 Fetching GeeksforGeeks stats for {username}...")
    
    try:
        url = f"https://auth.geeksforgeeks.org/user/{username}/practice/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=25)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            current_time = get_local_time()
            stats = {
                'username': username,
                'problems_solved': 0,
                'coding_score': 0,
                'institute_rank': 'N/A',
                'difficulty_breakdown': {
                    'school': 0,
                    'basic': 0,
                    'easy': 0,
                    'medium': 0,
                    'hard': 0
                },
                'last_updated': current_time.strftime('%Y-%m-%d %H:%M:%S IST'),
                'last_updated_utc': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
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
                '.profile-stat-value',
                '.score-card__content .score-card__value'
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
                            if num > problems_solved and num < 10000:
                                problems_solved = num
                        except ValueError:
                            continue
            
            # Look for embedded JSON in script tags
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and ('problemsSolved' in script.string or 'problems_solved' in script.string):
                    json_matches = re.findall(r'"(?:problemsSolved|problems_solved)"\s*:\s*(\d+)', script.string)
                    if json_matches:
                        try:
                            problems_solved = max(problems_solved, int(json_matches[0]))
                        except ValueError:
                            continue
            
            stats['problems_solved'] = problems_solved
            
            # Save to platform stats
            os.makedirs('data/platform_stats', exist_ok=True)
            with open('data/platform_stats/geeksforgeeks_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
            
            print(f"✅ GeeksforGeeks: {stats['problems_solved']} problems solved")
            return stats
            
    except Exception as e:
        print(f"❌ Error fetching GeeksforGeeks stats: {e}")
        
    # Return minimal stats to prevent crashes
    return {
        'username': username,
        'problems_solved': 0,
        'coding_score': 0,
        'last_updated': get_local_time().strftime('%Y-%m-%d %H:%M:%S IST'),
        'last_updated_utc': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    }

def fetch_hackerrank_stats(username="bxlz_14"):
    """Fetch HackerRank user statistics with better parsing"""
    print(f"⭐ Fetching HackerRank stats for {username}...")
    
    try:
        url = f"https://www.hackerrank.com/profile/{username}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            current_time = get_local_time()
            stats = {
                'username': username,
                'badges': 0,
                'gold_badges': 0,
                'silver_badges': 0,
                'bronze_badges': 0,
                'problems_solved': 0,
                'domains': [],
                'last_updated': current_time.strftime('%Y-%m-%d %H:%M:%S IST'),
                'last_updated_utc': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            }
            
            # Enhanced badge detection
            badge_elements = soup.find_all(['div', 'span'], class_=re.compile(r'badge', re.I))
            if badge_elements:
                stats['badges'] = len([elem for elem in badge_elements if elem.get_text().strip()])
            
            # Look for problems solved
            problem_elements = soup.find_all(text=re.compile(r'\d+.*(?:problem|challenge).*solved', re.I))
            for elem in problem_elements:
                numbers = re.findall(r'\d+', elem)
                if numbers:
                    stats['problems_solved'] = int(numbers[0])
                    break
            
            # Save to platform stats
            os.makedirs('data/platform_stats', exist_ok=True)
            with open('data/platform_stats/hackerrank_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
                
            print(f"✅ HackerRank: {stats['badges']} badges, {stats['problems_solved']} problems")
            return stats
            
    except Exception as e:
        print(f"❌ Error fetching HackerRank stats: {e}")
        
    # Return default stats
    return {
        'username': username,
        'badges': 0,
        'problems_solved': 0,
        'last_updated': get_local_time().strftime('%Y-%m-%d %H:%M:%S IST'),
        'last_updated_utc': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    }

def calculate_daily_progress():
    """Calculate today's progress compared to yesterday"""
    print("📅 Calculating daily progress...")
    
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    current_time = get_local_time()
    
    # Load current stats
    current_stats = {}
    platforms = ['leetcode', 'geeksforgeeks', 'hackerrank']
    
    for platform in platforms:
        try:
            with open(f'data/platform_stats/{platform}_stats.json', 'r') as f:
                current_stats[platform] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            current_stats[platform] = {}
    
    # Load yesterday's progress if exists
    yesterday_progress = {}
    try:
        with open(f'data/daily_progress/{yesterday}.json', 'r') as f:
            yesterday_data = json.load(f)
            yesterday_progress = yesterday_data.get('platform_totals', {})
    except (FileNotFoundError, json.JSONDecodeError):
        yesterday_progress = {}
    
    # Calculate today's progress
    daily_progress = {
        'date': today,
        'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S IST'),
        'timestamp_utc': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'platform_totals': {},
        'daily_gains': {},
        'problems_solved_today': 0,
        'summary': {
            'total_platforms_active': 0,
            'most_active_platform': '',
            'daily_streak': 0
        }
    }
    
    total_problems_today = 0
    platform_gains = {}
    
    # Calculate gains for each platform
    if current_stats.get('leetcode', {}).get('solved_problems', {}):
        lc_total = current_stats['leetcode']['solved_problems']['total']
        lc_yesterday = yesterday_progress.get('leetcode', 0)
        lc_gain = max(0, lc_total - lc_yesterday)
        
        daily_progress['platform_totals']['leetcode'] = lc_total
        daily_progress['daily_gains']['leetcode'] = lc_gain
        total_problems_today += lc_gain
        platform_gains['leetcode'] = lc_gain
    
    if current_stats.get('geeksforgeeks', {}).get('problems_solved'):
        gfg_total = current_stats['geeksforgeeks']['problems_solved']
        gfg_yesterday = yesterday_progress.get('geeksforgeeks', 0)
        gfg_gain = max(0, gfg_total - gfg_yesterday)
        
        daily_progress['platform_totals']['geeksforgeeks'] = gfg_total
        daily_progress['daily_gains']['geeksforgeeks'] = gfg_gain
        total_problems_today += gfg_gain
        platform_gains['geeksforgeeks'] = gfg_gain
    
    if current_stats.get('hackerrank', {}).get('problems_solved'):
        hr_total = current_stats['hackerrank']['problems_solved']
        hr_yesterday = yesterday_progress.get('hackerrank', 0)
        hr_gain = max(0, hr_total - hr_yesterday)
        
        daily_progress['platform_totals']['hackerrank'] = hr_total
        daily_progress['daily_gains']['hackerrank'] = hr_gain
        total_problems_today += hr_gain
        platform_gains['hackerrank'] = hr_gain
    
    daily_progress['problems_solved_today'] = total_problems_today
    
    # Calculate summary stats
    active_platforms = sum(1 for gain in platform_gains.values() if gain > 0)
    daily_progress['summary']['total_platforms_active'] = active_platforms
    
    if platform_gains:
        most_active = max(platform_gains.items(), key=lambda x: x[1])
        daily_progress['summary']['most_active_platform'] = most_active[0] if most_active[1] > 0 else ''
    
    # Save today's progress
    os.makedirs('data/daily_progress', exist_ok=True)
    with open(f'data/daily_progress/{today}.json', 'w') as f:
        json.dump(daily_progress, f, indent=2)
    
    print(f"✅ Daily Progress: {total_problems_today} problems solved today across {active_platforms} platforms")
    return daily_progress

def generate_enhanced_readme():
    """Generate README with enhanced UI and daily progress tracking"""
    print("📝 Generating enhanced README with daily progress...")
    
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except FileNotFoundError:
        print("❌ README.md not found")
        return
    
    # Load today's progress
    today = datetime.now().strftime('%Y-%m-%d')
    daily_progress = {}
    try:
        with open(f'data/daily_progress/{today}.json', 'r') as f:
            daily_progress = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        daily_progress = {}
    
    # Load platform stats
    platform_stats = {}
    platforms = ['leetcode', 'geeksforgeeks', 'hackerrank']
    for platform in platforms:
        try:
            with open(f'data/platform_stats/{platform}_stats.json', 'r') as f:
                platform_stats[platform] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            platform_stats[platform] = {}
    
    # Get IST time for display
    ist_time = get_local_time()
    display_time = ist_time.strftime('%Y-%m-%d %H:%M IST')
    
    # Create enhanced stats section with beautiful UI
    stats_section = f"""## 📊 Daily Coding Progress & Stats

<div align="center">

### 🌙 Today's Progress - {today}
<table>
<tr>
<td align="center" width="25%">
<img src="https://img.shields.io/badge/Problems%20Solved%20Today-{daily_progress.get('problems_solved_today', 0)}-brightgreen?style=for-the-badge&logo=checkmarx&logoColor=white"/>
</td>
<td align="center" width="25%">
<img src="https://img.shields.io/badge/Active%20Platforms-{daily_progress.get('summary', {}).get('total_platforms_active', 0)}-blue?style=for-the-badge&logo=buffer&logoColor=white"/>
</td>
<td align="center" width="25%">
<img src="https://img.shields.io/badge/Last%20Updated-{ist_time.strftime('%H:%M')}-orange?style=for-the-badge&logo=clock&logoColor=white"/>
</td>
<td align="center" width="25%">
<img src="https://img.shields.io/badge/Auto%20Update-10:00%20PM-purple?style=for-the-badge&logo=github-actions&logoColor=white"/>
</td>
</tr>
</table>

### 📈 Platform Statistics & Daily Progress

| Platform | Today's Gain | Total Solved | Breakdown | Profile |
|----------|-------------|--------------|-----------|---------|"""

    # LeetCode row
    lc_stats = platform_stats.get('leetcode', {})
    lc_gain = daily_progress.get('daily_gains', {}).get('leetcode', 0)
    if lc_stats and lc_stats.get('solved_problems', {}).get('total', 0) > 0:
        lc = lc_stats['solved_problems']
        gain_badge = f"🔥 **+{lc_gain}**" if lc_gain > 0 else "➖ **0**"
        ranking_text = f"#{lc_stats.get('ranking', 'N/A')}" if lc_stats.get('ranking') != 'N/A' else 'Unranked'
        
        stats_section += f"""
| 🔥 **LeetCode** | {gain_badge} | **{lc['total']}** | Easy: {lc['easy']} \\| Medium: {lc['medium']} \\| Hard: {lc['hard']}<br/>Ranking: {ranking_text} | [bxlz14](https://leetcode.com/bxlz14) |"""
    else:
        stats_section += """
| 🔥 **LeetCode** | 🔄 Loading... | **Loading...** | Fetching latest stats... | [bxlz14](https://leetcode.com/bxlz14) |"""

    # GeeksforGeeks row
    gfg_stats = platform_stats.get('geeksforgeeks', {})
    gfg_gain = daily_progress.get('daily_gains', {}).get('geeksforgeeks', 0)
    if gfg_stats and gfg_stats.get('problems_solved', 0) > 0:
        gain_badge = f"🚀 **+{gfg_gain}**" if gfg_gain > 0 else "➖ **0**"
        stats_section += f"""
| 🚀 **GeeksforGeeks** | {gain_badge} | **{gfg_stats['problems_solved']}** | Coding Score: {gfg_stats.get('coding_score', 0)}<br/>Multi-difficulty problems | [bxlz14](https://auth.geeksforgeeks.org/user/bxlz14) |"""
    else:
        stats_section += """
| 🚀 **GeeksforGeeks** | 🔄 Loading... | **Loading...** | Fetching latest stats... | [bxlz14](https://auth.geeksforgeeks.org/user/bxlz14) |"""

    # HackerRank row
    hr_stats = platform_stats.get('hackerrank', {})
    hr_gain = daily_progress.get('daily_gains', {}).get('hackerrank', 0)
    if hr_stats and hr_stats.get('badges', 0) > 0:
        gain_badge = f"⭐ **+{hr_gain}**" if hr_gain > 0 else "➖ **0**"
        stats_section += f"""
| ⭐ **HackerRank** | {gain_badge} | **{hr_stats['badges']}** badges | Problems: {hr_stats.get('problems_solved', 0)}<br/>🥇 {hr_stats.get('gold_badges', 0)} \\| 🥈 {hr_stats.get('silver_badges', 0)} \\| 🥉 {hr_stats.get('bronze_badges', 0)} | [bxlz_14](https://www.hackerrank.com/bxlz_14) |"""
    else:
        stats_section += """
| ⭐ **HackerRank** | 🔄 Loading... | **Loading...** | Fetching latest stats... | [bxlz_14](https://www.hackerrank.com/bxlz_14) |"""

    # Add Codolio tracker
    stats_section += """
| 🔗 **Codolio** | 📊 **Tracker** | **Multi-Platform** | Unified progress dashboard<br/>Real-time sync across platforms | [bxlz.14](https://codolio.com/profile/bxlz.14) |

</div>

### 🎯 Progress Summary

<div align="center">

<table>
<tr>
<td align="center" width="50%">
<h4>📅 Today's Activity</h4>"""

    # Today's activity breakdown
    if daily_progress:
        if daily_progress.get('problems_solved_today', 0) > 0:
            stats_section += f"""
<img src="https://img.shields.io/badge/🔥_LeetCode-+{daily_progress.get('daily_gains', {}).get('leetcode', 0)}-ff6b6b?style=flat-square"/>
<img src="https://img.shields.io/badge/🚀_GeeksforGeeks-+{daily_progress.get('daily_gains', {}).get('geeksforgeeks', 0)}-4caf50?style=flat-square"/>
<img src="https://img.shields.io/badge/⭐_HackerRank-+{daily_progress.get('daily_gains', {}).get('hackerrank', 0)}-ffc107?style=flat-square"/>
<br/>
<img src="https://img.shields.io/badge/Total%20Today-{daily_progress.get('problems_solved_today', 0)}%20problems-brightgreen?style=for-the-badge&logo=target&logoColor=white"/>"""
        else:
            stats_section += """
<img src="https://img.shields.io/badge/Today-Rest%20Day-lightgrey?style=for-the-badge&logo=coffee&logoColor=white"/>
<br/>
<sub>🌙 Ready for tomorrow's challenges!</sub>"""
    else:
        stats_section += """
<img src="https://img.shields.io/badge/Status-Syncing...-yellow?style=for-the-badge&logo=refresh&logoColor=white"/>"""

    stats_section += """
</td>
<td align="center" width="50%">
<h4>📊 Overall Progress</h4>"""

    # Calculate total problems
    total_problems = 0
    if platform_stats.get('leetcode', {}).get('solved_problems', {}):
        total_problems += platform_stats['leetcode']['solved_problems']['total']
    if platform_stats.get('geeksforgeeks', {}).get('problems_solved', 0):
        total_problems += platform_stats['geeksforgeeks']['problems_solved']
    if platform_stats.get('hackerrank', {}).get('problems_solved', 0):
        total_problems += platform_stats['hackerrank']['problems_solved']

    stats_section += f"""
<img src="https://img.shields.io/badge/Total%20Solved-{total_problems}%2B-blue?style=for-the-badge&logo=trophy&logoColor=white"/>
<br/>
<img src="https://img.shields.io/badge/Platforms-3%20Active-purple?style=flat-square&logo=buffer"/>
<img src="https://img.shields.io/badge/Auto%20Update-Daily%2010PM-orange?style=flat-square&logo=clock"/>
</td>
</tr>
</table>

<sub>🌙 <em>Last Updated: {display_time} | Auto-updated daily at 10:00 PM IST</em></sub>
<br/>
<sub>📈 <em>Tracking daily progress and cumulative achievements across all platforms</em></sub>

</div>"""

    # Update README with enhanced stats section
    pattern = r'## 📊 (?:Current Coding Stats|Daily Coding Progress).*?(?=## [🎓💻🏅]|$)'
    
    if re.search(pattern, readme_content, re.DOTALL):
        readme_content = re.sub(pattern, stats_section.strip() + '\n\n', readme_content, flags=re.DOTALL)
    else:
        # Find a good place to insert the stats section
        competitive_pattern = r'(### Codolio Profile.*?</div>)'
        if re.search(competitive_pattern, readme_content, re.DOTALL):
            readme_content = re.sub(
                competitive_pattern, 
                r'\1\n\n' + stats_section + '\n', 
                readme_content, 
                flags=re.DOTALL
            )
        else:
            # Insert before tech stack
            tech_pattern = r'(## 💻 Tech Stack)'
            if re.search(tech_pattern, readme_content):
                readme_content = re.sub(
                    tech_pattern,
                    stats_section + '\n\n' + r'\1',
                    readme_content
                )

    # Write the updated README
    try:
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("✅ README.md updated with enhanced daily progress UI!")
    except Exception as e:
        print(f"❌ Error writing README: {e}")

def cleanup_old_progress_files():
    """Clean up progress files older than 30 days"""
    print("🧹 Cleaning up old progress files...")
    
    progress_dir = 'data/daily_progress'
    if not os.path.exists(progress_dir):
        return
    
    cutoff_date = datetime.now() - timedelta(days=30)
    files_cleaned = 0
    
    for filename in os.listdir(progress_dir):
        if filename.endswith('.json'):
            try:
                file_date = datetime.strptime(filename.replace('.json', ''), '%Y-%m-%d')
                if file_date < cutoff_date:
                    os.remove(os.path.join(progress_dir, filename))
                    files_cleaned += 1
            except ValueError:
                continue
    
    if files_cleaned > 0:
        print(f"🗑️ Cleaned up {files_cleaned} old progress files")

def main():
    """Main function to update daily stats and progress"""
    print("🌙 Starting daily coding progress update at 10:00 PM...")
    print("=" * 80)
    
    ist_time = get_local_time()
    print(f"🕙 Current IST Time: {ist_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 Current UTC Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    success_count = 0
    total_platforms = 3
    
    # Fetch stats from all platforms
    platform_results = {}
    
    try:
        print("\n🔥 LEETCODE UPDATE")
        print("-" * 40)
        lc_stats = fetch_leetcode_stats()
        if lc_stats and lc_stats['solved_problems']['total'] > 0:
            success_count += 1
            platform_results['leetcode'] = lc_stats
        time.sleep(2)  # Rate limiting
    except Exception as e:
        print(f"❌ LeetCode fetch failed: {e}")
    
    try:
        print("\n🚀 GEEKSFORGEEKS UPDATE")
        print("-" * 40)
        gfg_stats = fetch_geeksforgeeks_stats()
        if gfg_stats and gfg_stats['problems_solved'] >= 0:
            success_count += 1
            platform_results['geeksforgeeks'] = gfg_stats
        time.sleep(2)  # Rate limiting
    except Exception as e:
        print(f"❌ GeeksforGeeks fetch failed: {e}")
    
    try:
        print("\n⭐ HACKERRANK UPDATE")
        print("-" * 40)
        hr_stats = fetch_hackerrank_stats()
        if hr_stats:
            success_count += 1
            platform_results['hackerrank'] = hr_stats
        time.sleep(2)  # Rate limiting
    except Exception as e:
        print(f"❌ HackerRank fetch failed: {e}")
    
    # Calculate daily progress
    try:
        print("\n📅 DAILY PROGRESS CALCULATION")
        print("-" * 40)
        daily_progress = calculate_daily_progress()
        print(f"✅ Daily progress calculated and saved!")
    except Exception as e:
        print(f"❌ Daily progress calculation failed: {e}")
    
    # Update README with enhanced UI
    try:
        print("\n📝 README UPDATE")
        print("-" * 40)
        generate_enhanced_readme()
        print("✅ README updated with enhanced UI!")
    except Exception as e:
        print(f"❌ README update failed: {e}")
    
    # Cleanup old files
    try:
        cleanup_old_progress_files()
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    # Final summary
    print("\n" + "=" * 80)
    print(f"🌙 NIGHTLY UPDATE COMPLETE - {ist_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("=" * 80)
    print(f"📊 Platform Updates: {success_count}/{total_platforms} successful")
    
    if daily_progress:
        print(f"📈 Today's Progress: {daily_progress.get('problems_solved_today', 0)} problems solved")
        active_platforms = daily_progress.get('summary', {}).get('total_platforms_active', 0)
        print(f"🎯 Active Platforms: {active_platforms}")
        
        if daily_progress.get('summary', {}).get('most_active_platform'):
            print(f"🏆 Most Active: {daily_progress['summary']['most_active_platform'].title()}")
    
    print(f"🔄 Next Update: Tomorrow at 10:00 PM IST")
    print("✨ Enhanced UI with daily progress tracking active!")
    print("=" * 80)

if __name__ == "__main__":
    main()