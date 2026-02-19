# 🎵 Type Beat Classifier - DEMO INSTRUCTIONS

## 🚀 Quick Start Demo

You have **697 trained fingerprints** from **74 artists** ready to use!

### Option 1: Command Line Demo (Fastest)

```bash
cd "/Users/sskmusic/Type beat/ml"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate typebeat

# Classify a song
python demo_classifier.py /path/to/your/song.mp3

# Or run interactively
python demo_classifier.py
```

**Example Output:**
```
🎯 TOP 10 ARTIST MATCHES
============================================================

 1. Drake                             85.3% [████████████████████████████████████████████░░░░] (10 fingerprints)
 2. Travis Scott                      82.1% [████████████████████████████████████████░░░░░░░░] (10 fingerprints)
 3. Metro Boomin                      79.5% [████████████████████████████████████░░░░░░░░░░░░] (10 fingerprints)
...
```

### Option 2: Streamlit Dashboard (Visual)

```bash
cd "/Users/sskmusic/Type beat/ml"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate typebeat

# Start dashboard
streamlit run training_dashboard.py --server.port 8501
```

Then open: **http://localhost:8501**

**Features:**
- 📊 View training statistics
- 🎨 Visualize fingerprints (mel-spectrograms)
- 🔍 Explore trained artists
- ✨ Generate 3D visualizations with Gemini AI

### Option 3: Full Web App (Production UI)

```bash
# Terminal 1: Start Backend
cd "/Users/sskmusic/Type beat/backend"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate typebeat
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start Frontend
cd "/Users/sskmusic/Type beat/frontend"
npm run dev
```

Then open: **http://localhost:3000**

**Features:**
- 🎵 Drag & drop audio upload
- 🔍 Real-time fingerprint matching
- 📈 Trending artist data
- 🎯 Similarity scores

---

## 📋 Trained Artists List

You have **697 fingerprints** from **74 artists**:

### ✅ Fully Trained (10+ fingerprints each):
1. 21 Savage
2. A$AP Rocky
3. Anuel AA
4. Ariana Grande
5. Bad Bunny
6. Billie Eilish
7. Cardi B
8. DaBaby
9. Destroy Lonely
10. Doja Cat
11. Don Toliver
12. Drake
13. Eslabon Armado
14. Feid
15. Fuerza Regida
16. Future
17. Gunna
18. Ice Spice
19. J Balvin
20. J. Cole
21. Jack Harlow
22. Juice WRLD
23. Kanye West
24. Karol G
25. Ken Carson
26. Kendrick Lamar
27. Kodak Black
28. Lancey Foux
29. Latto
30. Lil Baby
31. Lil Durk
32. Lil Nas X
33. Lil Tecca
34. Lil Tjay
35. Lil Uzi Vert
36. Lil Wayne
37. Lil Yachty
38. Maluma
39. Megan Thee Stallion
40. Metro Boomin
41. Migos
42. Myke Towers
43. Nicki Minaj
44. NLE Choppa
45. Offset
46. Olivia Rodrigo
47. Ozuna
48. Peso Pluma
49. Playboi Carti
50. Polo G
51. Pooh Shiesty
52. Post Malone
53. Quavo
54. Rauw Alejandro
55. Roddy Ricch
56. SoFaygo
57. SSGKobe
58. Summrs
59. SZA
60. Takeoff
61. Taylor Swift
62. Travis Scott
63. Tyler The Creator
64. Yeat
65. Young Thug

### 🔄 Partially Trained:
- 42 Dugg (4)
- Autumn! (7)
- Babyface Ray (7)
- BabyTron (3)
- EST Gee (4)
- Lucki (9)
- Moneybagg Yo (3)
- Rio Da Yung OG (6)
- Sada Baby (4)

---

## 🎯 Demo Tips

### Best Demo Songs:
- **Drake-style beats**: Trap, melodic, 70-85 BPM
- **Travis Scott-style**: Dark, atmospheric, 70-80 BPM
- **Metro Boomin-style**: Heavy 808s, trap, 65-75 BPM
- **Lil Baby-style**: Fast trap, 75-85 BPM

### What to Say:
1. **"I've trained a neural audio fingerprint system on 697 songs from 74 top artists"**
2. **"It uses mel-spectrograms and cosine similarity to match your beat"**
3. **"The system identifies which artist's style your beat sounds most like"**
4. **"All training data came from top-performing official songs on YouTube"**

### Demo Flow:
1. **Show the trained artists list** (impressive!)
2. **Upload a beat** (use command line or web UI)
3. **Show top matches** with similarity scores
4. **Explain the technology**: Neural fingerprints, mel-spectrograms, vector similarity

---

## 🔧 Troubleshooting

### "Training data not found"
```bash
# Check if file exists
ls -lh ml/data/training_fingerprints/final_training_data_1000.json

# If missing, use latest batch file
python demo_classifier.py song.mp3 --training-data ml/data/training_fingerprints/training_batch_90.json
```

### "Error generating fingerprint"
- Make sure `librosa` is installed: `conda install -c conda-forge librosa`
- Check audio file format (MP3, WAV, M4A supported)

### "No matches found"
- Check that training data has fingerprints (not empty)
- Try lowering similarity threshold in code

---

## 📊 Training Stats

- **Total Fingerprints**: 697
- **Unique Artists**: 74
- **Fully Completed**: 65 artists (10+ each)
- **Partially Completed**: 9 artists
- **Data Source**: YouTube (top-performing official songs)
- **Fingerprint Method**: Neural Audio FP (128-dim embeddings)

---

## 🎤 Conference Demo Script

**Opening:**
> "I've built a type beat classifier that uses neural audio fingerprints to identify which artist's style a beat sounds like. I've trained it on 697 songs from 74 top artists including Drake, Travis Scott, Metro Boomin, and more."

**Demo:**
> "Let me upload a beat and see what it matches..."

**Results:**
> "The system found that this beat is 85% similar to Drake's style, 82% similar to Travis Scott, and 79% similar to Metro Boomin. This uses mel-spectrograms and cosine similarity in a 128-dimensional embedding space."

**Close:**
> "The system is production-ready and can be used to help producers optimize their beats for specific artist styles and market trends."

---

**Good luck with your demo! 🚀**
