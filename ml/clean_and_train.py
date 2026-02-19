"""
Clean discovered artists and run fingerprint training
"""

import json
import re
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.dirname(__file__))

from hybrid_trainer import HybridTrainer

# Load env
env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(env_path)


def get_curated_artists() -> list:
    """Get curated list of top 100 real artists"""
    curated_file = Path(__file__).parent.parent / "data" / "top_100_real_artists.json"
    if curated_file.exists():
        with open(curated_file, 'r') as f:
            data = json.load(f)
        return [{'name': name, 'type_beat_count': 0, 'total_views': 0, 'priority': 1} 
                for name in data.get('artists', [])]
    return []


def clean_artists(input_file: str = "data/trending_artists.json") -> list:
    """Clean and extract top 100 unique artists"""
    
    # Load results
    file_path = Path(__file__).parent / input_file
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return []
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Known real artists (to prioritize)
    known_artists = {
        'lil baby', 'travis scott', 'drake', 'metro boomin', '21 savage', 'jack harlow',
        'lil tecca', 'don toliver', 'duki', 'shoreline mafia', 'finesse2tymes', 'lil tjay',
        'polo g', 'mo3', 'gunna', 'future', 'lil yachty', 'veeze', 'rylo rodriguez',
        'young nudy', 'lucki', 'asap rocky', 'pasta', 'playboi carti', 'chess', 'kay flock',
        'sha ek', 'juice wrld', 'pooh shiesty', 'tyga', 'fivio foreign', 'meek mill',
        'bossman dlow', 'j.i', 'hamza', 'big yavo', 'aaron may', 'isaiah rashad',
        'j. cole', 'kendrick lamar', 'jid', 'macklemore', 'vonoff1700', 'bigxthaplug',
        'nle choppa', 'sleazyworld go', 'kodak black', 'g herbo', 'lithe', 'splurge',
        'key glock', 'young dolph', 'mf doom', 'joey bada$$', 'bak jay', '50 cent',
        'strandz', 'big30', 'lil double 0', 'nemzzz', 'lil tony', 'blp kosher',
        'kanye west', 'kendrick', 'cole', 'eminem', 'lil wayne', 'future', 'lil uzi vert',
        'playboi carti', 'yeat', 'ice spice', 'latto', 'doja cat', 'megan thee stallion'
    }
    
    # Generic terms to exclude
    generic = [
        'trap', 'freestyle', 'dark', 'hard', 'melodic', 'sad', 'diss', 'rap',
        'boom bap', 'instrumental', 'beat', 'radio', 'lo-fi', 'lofi', 'chill',
        'synthwave', 'free', 'sample', 'year', 'hour', 'mix', 'beats', 'track',
        'old school', 'new jazz', 'uk drill', 'detroit', 'bouncy', 'sold',
        'for profit', 'free use', 'uso libre', 'anabolic', 'beatz', 'jazz',
        'hip hop', 'hiphop', 'emotional', 'piano', 'ballad', 'acoustic',
        'guitar', 'drill', 'ny drill', 'chicago drill', 'jerk drill',
        'indian', 'brazilian funk', 'rnb', 'r&b', 'style', 'storytelling',
        'orchestra', 'sob', 'sax', 'karma', 'boxed in', 'yedi yung',
        'no passes', 'we try making a wii', 'bro is making it out the suburbs',
        'emotional piano', 'acoustic guitar', 'piano ballad'
    ]
    
    artists_clean = []
    seen = set()
    
    for artist_data in data.get('artists', []):
        name = artist_data['name'].strip()
        
        # Clean HTML and special chars
        name = name.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
        name = re.sub(r'[\[\]()]', '', name)  # Remove brackets/parentheses
        
        # Skip if contains special formatting
        if any(char in name.lower() for char in ['#', '<', '>', '🔥', '🍐', '📚', '🌌', '🐾']):
            continue
        
        name_lower = name.lower().strip()
        
        # Skip generic terms
        if any(term in name_lower for term in generic):
            continue
        
        # Normalize
        name_normalized = ' '.join(word.capitalize() for word in name.split())
        
        # Handle collaborations (X) - take first artist
        if ' X ' in name_normalized.upper() or ' x ' in name_normalized:
            parts = re.split(r'\s+[Xx]\s+', name_normalized)
            name_normalized = parts[0].strip()
        
        # Skip if too short
        if len(name_normalized) < 3:
            continue
        
        # Deduplicate
        name_key = name_normalized.lower()
        if name_key not in seen:
            seen.add(name_key)
            priority = 1 if name_key in known_artists else 0
            artists_clean.append({
                'name': name_normalized,
                'type_beat_count': artist_data.get('type_beat_count', 0),
                'total_views': artist_data.get('total_views', 0),
                'priority': priority
            })
    
    # Sort: known artists first, then by popularity
    artists_clean.sort(key=lambda x: (-x['priority'], x['type_beat_count'], x['total_views']), reverse=True)
    
    return artists_clean[:100]


def main():
    """Main function"""
    print("🔍 Getting top 100 artists...")
    
    # Try curated list first (most reliable)
    artists = get_curated_artists()
    
    # Fallback to discovered artists if curated not available
    if not artists:
        print("   Using discovered artists (cleaning...)")
        artists = clean_artists()
    
    if not artists:
        print("❌ No artists found. Run discovery first or use curated list.")
        return
    
    print(f"✅ Found {len(artists)} unique artists")
    print(f"\nTop 30 artists:")
    for i, a in enumerate(artists[:30], 1):
        print(f"{i:3}. {a['name']:<30} ({a['type_beat_count']} beats, {a['total_views']:,} views)")
    
    # Save cleaned list
    output_path = Path("data/top_100_artists_clean.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({'artists': artists, 'total': len(artists)}, f, indent=2)
    print(f"\n💾 Saved to {output_path}")
    
    # Extract artist names
    artist_names = [a['name'] for a in artists]
    print(f"\n📋 Training on {len(artist_names)} artists (10 fingerprints each = {len(artist_names) * 10} total)")
    print(f"\nFirst 20: {', '.join(artist_names[:20])}")
    
    # Ask for confirmation
    print("\n🚀 Starting fingerprint extraction...")
    print("   This will download top-performing official songs for each artist")
    print("   Videos prioritized by: views + comments (high engagement)")
    print("   Target: 10 fingerprints per artist = 1000 total\n")
    
    # Initialize trainer
    spotify_id = os.getenv("SPOTIFY_CLIENT_ID")
    spotify_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    trainer = HybridTrainer(spotify_id, spotify_secret)
    
    # Train on all artists (10 per artist)
    total_fingerprints = 0
    for i, artist in enumerate(artist_names, 1):
        print(f"\n[{i}/{len(artist_names)}] 🎵 Training on: {artist}")
        count = trainer.train_artist_hybrid(artist, max_items=10)
        total_fingerprints += count
        print(f"   ✅ Generated {count} fingerprints (Total: {total_fingerprints})")
        
        # Save incrementally every 10 artists
        if i % 10 == 0:
            trainer.save_training_data(f"training_batch_{i}.json")
            print(f"   💾 Saved checkpoint")
    
    # Final save
    trainer.save_training_data("final_training_data_1000.json")
    print(f"\n✅ Training complete!")
    print(f"   Total fingerprints: {total_fingerprints}")
    print(f"   Target was: {len(artist_names) * 10}")
    print(f"   Saved to: data/training_fingerprints/final_training_data_1000.json")


if __name__ == "__main__":
    main()
