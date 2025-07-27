# scripts/update_stats.py
import requests
import json
import os
from datetime import datetime
import re
from bs4 import BeautifulSoup

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
            timeout=10
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
                    }
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
    """Fetch GeeksforGeeks user statistics"""
    print(f"Fetching GeeksforGeeks stats for {username}...")
    
    try:
        url = f"https://auth.geeksforgeeks.org/user/{username}/practice/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            stats = {
                'username': username,
                'problems_solved': 0,
                'coding_score': 0,
                'institute_rank': 'N/A'
            }
            
            # Try to extract stats from the page
            # This is a basic implementation - GeeksforGeeks structure may vary
            problem_count = soup.find_all('span', class_='score_card_value')
            if problem_count:
                try:
                    stats['problems_solved'] = int(problem_count[0].text.strip())
                except (ValueError, IndexError):
                    pass
            
            # Save to file
            os.makedirs('data', exist_ok=True)
            with open('data/geeksforgeeks_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
                
            print(f"✅ GeeksforGeeks stats updated: {stats['problems_solved']} problems solved")
            return stats
            
    except Exception as e:
        print(f"❌ Error fetching GeeksforGeeks stats: {e}")
        return None

def fetch_hackerrank_stats(username="bxlz_14"):
    """Fetch HackerRank user statistics"""
    print(f"Fetching HackerRank stats for {username}...")
    
    try:
        url = f"https://www.hackerrank.com/rest/hackers/{username}/badges"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            stats = {
                'username': username,
                'badges': len(data.get('models', [])),
                'gold_badges': 0,
                'silver_badges': 0,
                'bronze_badges': 0
            }
            
            # Count badges by type
            for badge in data.get('models', []):
                badge_type = badge.get('badge', {}).get('level', '').lower()
                if 'gold' in badge_type:
                    stats['gold_badges'] += 1
                elif 'silver' in badge_type:
                    stats['silver_badges'] += 1
                elif 'bronze' in badge_type:
                    stats['bronze_badges'] += 1
            
            # Save to file
            os.makedirs('data', exist_ok=True)
            with open('data/hackerrank_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
                
            print(f"✅ HackerRank stats updated: {stats['badges']} badges earned")
            return stats
            
    except Exception as e:
        print(f"❌ Error fetching HackerRank stats: {e}")
        return None

def generate_readme_with_stats():
    """Generate README with updated stats"""
    print("Generating updated README...")
    
    # Load all stats
    stats = {}
    
    # Load LeetCode stats
    try:
        with open('data/leetcode_stats.json', 'r') as f:
            stats['leetcode'] = json.load(f)
    except FileNotFoundError:
        stats['leetcode'] = None
    
    # Load GeeksforGeeks stats
    try:
        with open('data/geeksforgeeks_stats.json', 'r') as f:
            stats['geeksforgeeks'] = json.load(f)
    except FileNotFoundError:
        stats['geeksforgeeks'] = None
    
    # Load HackerRank stats
    try:
        with open('data/hackerrank_stats.json', 'r') as f:
            stats['hackerrank'] = json.load(f)
    except FileNotFoundError:
        stats['hackerrank'] = None
    
    # Read current README
    try:
        with open('README.md', 'r') as f:
            readme_content = f.read()
    except FileNotFoundError:
        print("❌ README.md not found")
        return
    
    # Update stats section in README
    stats_section = f"""
## 📊 Current Coding Stats (Updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')})

<div align="center">
  
| Platform | Stats | Profile |
|----------|--------|---------|
"""

    if stats['leetcode']:
        lc = stats['leetcode']
        stats_section += f"| 🔥 **LeetCode** | **{lc['solved_problems']['total']}** problems solved<br/>Easy: {lc['solved_problems']['easy']} \\| Medium: {lc['solved_problems']['medium']} \\| Hard: {lc['solved_problems']['hard']}<br/>Ranking: #{lc.get('ranking', 'N/A')} | [bxlz14](https://leetcode.com/bxlz14) |\n"
    else:
        stats_section += "| 🔥 **LeetCode** | Stats Loading... | [bxlz14](https://leetcode.com/bxlz14) |\n"
    
    if stats['geeksforgeeks']:
        gfg = stats['geeksforgeeks']
        stats_section += f"| 🚀 **GeeksforGeeks** | **{gfg['problems_solved']}** problems solved<br/>Coding Score: {gfg['coding_score']} | [bxlz14](https://auth.geeksforgeeks.org/user/bxlz14) |\n"
    else:
        stats_section += "| 🚀 **GeeksforGeeks** | Stats Loading... | [bxlz14](https://auth.geeksforgeeks.org/user/bxlz14) |\n"
    
    if stats['hackerrank']:
        hr = stats['hackerrank']
        stats_section += f"| ⭐ **HackerRank** | **{hr['badges']}** badges earned<br/>🥇 {hr['gold_badges']} \\| 🥈 {hr['silver_badges']} \\| 🥉 {hr['bronze_badges']} | [bxlz_14](https://www.hackerrank.com/bxlz_14) |\n"
    else:
        stats_section += "| ⭐ **HackerRank** | Stats Loading... | [bxlz_14](https://www.hackerrank.com/bxlz_14) |\n"
    
    stats_section += "| 🎯 **Codolio** | Multi-platform Tracker | [bxlz.14](https://codolio.com/profile/bxlz.14) |\n"
    stats_section += "\n</div>\n"
    
    # Find and replace the stats section in README
    # Look for the existing stats table and replace it
    pattern = r'## 📊 Current Coding Stats.*?</div>'
    
    if re.search(pattern, readme_content, re.DOTALL):
        readme_content = re.sub(pattern, stats_section.strip(), readme_content, flags=re.DOTALL)
    else:
        # If stats section doesn't exist, add it after the competitive programming section
        competitive_pattern = r'(## 🏆 Competitive Programming & Coding Platforms.*?</div>)'
        if re.search(competitive_pattern, readme_content, re.DOTALL):
            readme_content = re.sub(
                competitive_pattern, 
                r'\1\n\n' + stats_section, 
                readme_content, 
                flags=re.DOTALL
            )
    
    # Write updated README
    with open('README.md', 'w') as f:
        f.write(readme_content)
    
    print("✅ README.md updated with latest stats!")

def main():
    """Main function to update all stats"""
    print("🚀 Starting stats update process...")
    print("=" * 50)
    
    # Fetch stats from all platforms
    fetch_leetcode_stats()
    fetch_geeksforgeeks_stats()
    fetch_hackerrank_stats()
    
    # Update README with stats
    generate_readme_with_stats()
    
    print("=" * 50)
    print("✅ Stats update process completed!")

if __name__ == "__main__":
    main()
