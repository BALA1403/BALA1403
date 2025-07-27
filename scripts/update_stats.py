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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Debug: Print page title to verify we got the right page
            title = soup.find('title')
            print(f"Page title: {title.text if title else 'No title found'}")
            
            stats = {
                'username': username,
                'problems_solved': 0,
                'coding_score': 0,
                'institute_rank': 'N/A'
            }
            
            # Multiple selectors to try for problems solved
            selectors_to_try = [
                # Common selectors for GeeksforGeeks stats
                '.score_card_value',
                '.scoreCard_head_left--score__oSi_x',
                '.problemsSolved--count',
                '.problems-solved',
                '[data-testid="problems-solved"]',
                '.basicProfileDetailsLeft_head__MQVtS',
                '.solvedProblemCount',
                '.scoreCard_head_left__score',
                '.score-card-value',
                '.user-profile-stats .stat-value',
                '.stat-number',
                '.problems-count',
            ]
            
            problems_solved = 0
            
            # Try each selector
            for selector in selectors_to_try:
                elements = soup.select(selector)
                print(f"Trying selector '{selector}': found {len(elements)} elements")
                
                for elem in elements:
                    text = elem.get_text().strip()
                    print(f"Element text: '{text}'")
                    
                    # Extract number from text
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        try:
                            num = int(numbers[0])
                            if num > problems_solved:  # Take the highest number found
                                problems_solved = num
                                print(f"Found potential problems solved: {num}")
                        except ValueError:
                            continue
            
            # Alternative approach: Look for specific text patterns
            if problems_solved == 0:
                # Look for text containing "problems solved" or similar
                all_text = soup.get_text()
                patterns = [
                    r'(\d+)\s*problems?\s*solved',
                    r'solved\s*(\d+)\s*problems?',
                    r'(\d+)\s*coding\s*problems?',
                    r'problems?\s*solved:\s*(\d+)',
                    r'Total\s*Problems?\s*Solved[:\s]*(\d+)',
                    r'Problems?\s*Solved[:\s]*(\d+)',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, all_text, re.IGNORECASE)
                    if matches:
                        try:
                            problems_solved = int(matches[0])
                            print(f"Found via text pattern '{pattern}': {problems_solved}")
                            break
                        except ValueError:
                            continue
            
            # If still 0, try to find any number that might represent solved problems
            if problems_solved == 0:
                # Look for divs/spans with numbers that could be problem counts
                number_elements = soup.find_all(['div', 'span', 'p', 'h1', 'h2', 'h3'], string=re.compile(r'^\d+$'))
                print(f"Found {len(number_elements)} elements with just numbers")
                
                for elem in number_elements:
                    try:
                        num = int(elem.get_text().strip())
                        # Reasonable range for solved problems (not too high, not 0)
                        if 1 <= num <= 5000:
                            # Check if parent/sibling elements contain problem-related text
                            parent = elem.parent
                            context_text = ""
                            if parent:
                                context_text = parent.get_text().lower()
                                # Also check siblings
                                for sibling in parent.find_all():
                                    context_text += " " + sibling.get_text().lower()
                            
                            print(f"Checking number {num} with context: '{context_text[:100]}...'")
                            
                            if any(keyword in context_text for keyword in ['problem', 'solved', 'practice', 'coding', 'total', 'count']):
                                problems_solved = num
                                print(f"Found via context analysis: {num}")
                                break
                    except ValueError:
                        continue
            
            # Last resort: try to find script tags with JSON data
            if problems_solved == 0:
                script_tags = soup.find_all('script')
                for script in script_tags:
                    if script.string:
                        # Look for JSON-like data in script tags
                        if 'problemsSolved' in script.string or 'problems_solved' in script.string:
                            numbers = re.findall(r'"(?:problemsSolved|problems_solved)"\s*:\s*(\d+)', script.string)
                            if numbers:
                                try:
                                    problems_solved = int(numbers[0])
                                    print(f"Found in script tag: {problems_solved}")
                                    break
                                except ValueError:
                                    continue
            
            stats['problems_solved'] = problems_solved
            
            # Try to find coding score as well
            score_patterns = [
                r'coding\s*score[:\s]*(\d+)',
                r'score[:\s]*(\d+)',
                r'points?[:\s]*(\d+)',
                r'total\s*score[:\s]*(\d+)',
            ]
            
            all_text = soup.get_text()
            for pattern in score_patterns:
                matches = re.findall(pattern, all_text, re.IGNORECASE)
                if matches:
                    try:
                        stats['coding_score'] = int(matches[0])
                        print(f"Found coding score: {stats['coding_score']}")
                        break
                    except ValueError:
                        continue
            
            # Save to file
            os.makedirs('data', exist_ok=True)
            with open('data/geeksforgeeks_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
            
            print(f"✅ GeeksforGeeks stats updated: {stats['problems_solved']} problems solved")
            
            # If still 0, save the HTML for debugging
            if problems_solved == 0:
                with open('debug_gfg.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("❌ Could not find problems solved count. HTML saved to debug_gfg.html for analysis")
                
                # Print some sample text from the page for debugging
                sample_text = soup.get_text()[:1000]
                print(f"Sample page text: {sample_text}")
            
            return stats
            
    except Exception as e:
        print(f"❌ Error fetching GeeksforGeeks stats: {e}")
        return None

def fetch_hackerrank_stats(username="bxlz_14"):
    """Fetch HackerRank user statistics"""
    print(f"Fetching HackerRank stats for {username}...")
    
    try:
        # Try badges endpoint first
        url = f"https://www.hackerrank.com/rest/hackers/{username}/badges"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': f'https://www.hackerrank.com/profile/{username}',
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
                badge_info = badge.get('badge', {})
                badge_type = badge_info.get('level', '').lower()
                badge_name = badge_info.get('name', '').lower()
                
                if 'gold' in badge_type or 'gold' in badge_name:
                    stats['gold_badges'] += 1
                elif 'silver' in badge_type or 'silver' in badge_name:
                    stats['silver_badges'] += 1
                elif 'bronze' in badge_type or 'bronze' in badge_name:
                    stats['bronze_badges'] += 1
            
            # Save to file
            os.makedirs('data', exist_ok=True)
            with open('data/hackerrank_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
                
            print(f"✅ HackerRank stats updated: {stats['badges']} badges earned")
            return stats
        else:
            print(f"❌ HackerRank API returned status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error fetching HackerRank stats: {e}")
        
    # Fallback: try scraping the profile page
    try:
        print("Trying HackerRank profile page scraping as fallback...")
        url = f"https://www.hackerrank.com/profile/{username}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            stats = {
                'username': username,
                'badges': 0,
                'gold_badges': 0,
                'silver_badges': 0,
                'bronze_badges': 0
            }
            
            # Try to find badge information in the HTML
            badge_elements = soup.find_all(['div', 'span'], class_=re.compile(r'badge', re.I))
            stats['badges'] = len(badge_elements)
            
            # Save to file
            os.makedirs('data', exist_ok=True)
            with open('data/hackerrank_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
                
            print(f"✅ HackerRank stats updated (via scraping): {stats['badges']} badges found")
            return stats
            
    except Exception as e:
        print(f"❌ Error with HackerRank fallback scraping: {e}")
        return None

def fetch_tuf_stats(username="Luffy143"):
    """Fetch TakeUForward (TUF) user statistics"""
    print(f"Fetching TUF stats for {username}...")
    
    try:
        # TUF profile URL - adjust based on actual URL structure
        url = f"https://takeuforward.org/profile/{username}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        print(f"TUF Response status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            stats = {
                'username': username,
                'problems_solved': 0,
                'total_submissions': 0,
                'acceptance_rate': '0%',
                'progress_status': 'Active'
            }
            
            # Try to extract TUF-specific stats
            # These selectors may need adjustment based on actual TUF page structure
            selectors_patterns = [
                ('.problems-solved', r'(\d+)'),
                ('.total-submissions', r'(\d+)'),
                ('.acceptance-rate', r'(\d+(?:\.\d+)?)%'),
                ('.stat-value', r'(\d+)'),
                ('.progress-count', r'(\d+)'),
            ]
            
            page_text = soup.get_text()
            
            # Look for common patterns in the page text
            text_patterns = [
                (r'problems?\s*solved[:\s]*(\d+)', 'problems_solved'),
                (r'total\s*submissions?[:\s]*(\d+)', 'total_submissions'),
                (r'acceptance\s*rate[:\s]*(\d+(?:\.\d+)?)%', 'acceptance_rate'),
                (r'(\d+)\s*problems?\s*completed', 'problems_solved'),
                (r'(\d+)\s*questions?\s*solved', 'problems_solved'),
            ]
            
            for pattern, field in text_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    try:
                        if field == 'acceptance_rate':
                            stats[field] = f"{matches[0]}%"
                        else:
                            stats[field] = int(matches[0])
                        print(f"Found TUF {field}: {stats[field]}")
                        break
                    except (ValueError, IndexError):
                        continue
            
            # Try to find stats in HTML elements
            stat_elements = soup.find_all(['div', 'span', 'p'], text=re.compile(r'\d+'))
            for elem in stat_elements:
                text = elem.get_text().strip()
                if re.match(r'^\d+, text):
                    parent_text = elem.parent.get_text().lower() if elem.parent else ""
                    if any(keyword in parent_text for keyword in ['problem', 'solved', 'question', 'complete']):
                        try:
                            num = int(text)
                            if 0 <= num <= 2000:  # Reasonable range
                                stats['problems_solved'] = max(stats['problems_solved'], num)
                        except ValueError:
                            continue
            
            # Save to file
            os.makedirs('data', exist_ok=True)
            with open('data/tuf_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
                
            print(f"✅ TUF stats updated: {stats['problems_solved']} problems solved")
            return stats
        else:
            print(f"❌ TUF profile not accessible: {response.status_code}")
            # Return default stats if profile is not accessible
            default_stats = {
                'username': username,
                'problems_solved': 0,
                'total_submissions': 0,
                'acceptance_rate': '0%',
                'progress_status': 'Profile Private/Not Found'
            }
            
            # Save default stats
            os.makedirs('data', exist_ok=True)
            with open('data/tuf_stats.json', 'w') as f:
                json.dump(default_stats, f, indent=2)
            
            return default_stats
            
    except Exception as e:
        print(f"❌ Error fetching TUF stats: {e}")
        # Return default stats on error
        default_stats = {
            'username': username,
            'problems_solved': 0,
            'total_submissions': 0,
            'acceptance_rate': '0%',
            'progress_status': 'Error Fetching Data'
        }
        
        # Save default stats
        os.makedirs('data', exist_ok=True)
        with open('data/tuf_stats.json', 'w') as f:
            json.dump(default_stats, f, indent=2)
        
        return default_stats

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
    
    # Load TUF stats
    try:
        with open('data/tuf_stats.json', 'r') as f:
            stats['tuf'] = json.load(f)
    except FileNotFoundError:
        stats['tuf'] = None
    
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
    
    if stats['tuf']:
        tuf = stats['tuf']
        # Create comprehensive TUF stats display
        tuf_line = f"| 🎯 **TakeUForward** | **{tuf['problems_solved']}** problems solved"
        
        # Add breakdown if available
        if tuf['easy_solved'] + tuf['medium_solved'] + tuf['hard_solved'] > 0:
            tuf_line += f"<br/>Easy: {tuf['easy_solved']} \\| Medium: {tuf['medium_solved']} \\| Hard: {tuf['hard_solved']}"
        
        # Add progress info
        if tuf['progress_percentage'] > 0:
            tuf_line += f"<br/>Progress: {tuf['progress_percentage']}%"
        
        if tuf['current_streak'] > 0:
            tuf_line += f" \\| Streak: {tuf['current_streak']} days"
            
        if tuf['acceptance_rate'] != '0%':
            tuf_line += f"<br/>Acceptance Rate: {tuf['acceptance_rate']}"
            
        tuf_line += f" | [Luffy143](https://takeuforward.org/profile/Luffy143) |\n"
        stats_section += tuf_line
    else:
        stats_section += "| 🎯 **TakeUForward** | **Loading Stats...**<br/>DSA Progress Tracker<br/>Username: **Luffy143** | [Luffy143](https://takeuforward.org/profile/Luffy143) |\n"
    
    stats_section += "| 🔗 **Codolio** | Multi-platform Tracker | [bxlz.14](https://codolio.com/profile/bxlz.14) |\n"
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
        else:
            # If no competitive programming section, just append at the end
            readme_content += "\n\n" + stats_section
    
    # Write updated README
    with open('README.md', 'w') as f:
        f.write(readme_content)
    
    print("✅ README.md updated with latest stats!")

def fetch_tuf_alternative_stats(username="Luffy143"):
    """Alternative method to fetch TUF stats from SDE Sheet or A2Z DSA Course"""
    print(f"Trying alternative TUF stats for {username}...")
    
    # Try to get stats from TUF's popular sheets/courses
    alternative_urls = [
        "https://takeuforward.org/strivers-a2z-dsa-course/strivers-a2z-dsa-course-sheet-2/",
        "https://takeuforward.org/interviews/strivers-sde-sheet-top-coding-interview-problems/",
        f"https://takeuforward.org/profile/{username}/progress",
        f"https://takeuforward.org/user/{username}/submissions",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    for url in alternative_urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for progress indicators, completed problems, etc.
                progress_indicators = soup.find_all(['div', 'span', 'p'], 
                                                  text=re.compile(r'\d+.*(?:complete|solved|done)', re.I))
                
                if progress_indicators:
                    for indicator in progress_indicators:
                        text = indicator.get_text()
                        numbers = re.findall(r'\d+', text)
                        if numbers:
                            print(f"Found alternative TUF stat: {text}")
                            return {
                                'problems_solved': int(numbers[0]),
                                'source': 'alternative_method',
                                'url': url
                            }
        except Exception as e:
            print(f"Alternative method failed for {url}: {e}")
            continue
    
    return None

def main():
    """Main function to update all stats"""
    print("🚀 Starting stats update process...")
    print("=" * 50)
    
    # Fetch stats from all platforms
    fetch_leetcode_stats()
    fetch_geeksforgeeks_stats()
    fetch_hackerrank_stats()
    
    # Try primary TUF method
    tuf_stats = fetch_tuf_stats()
    
    # If primary method didn't get good stats, try alternative
    if tuf_stats and tuf_stats.get('problems_solved', 0) == 0:
        print("Trying alternative TUF stats method...")
        alt_stats = fetch_tuf_alternative_stats()
        if alt_stats:
            tuf_stats.update(alt_stats)
            # Save updated stats
            os.makedirs('data', exist_ok=True)
            with open('data/tuf_stats.json', 'w') as f:
                json.dump(tuf_stats, f, indent=2)
    
    # Update README with stats
    generate_readme_with_stats()
    
    print("=" * 50)
    print("✅ Stats update process completed!")

if __name__ == "__main__":
    main()
