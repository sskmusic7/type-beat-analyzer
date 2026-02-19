"""
Streamlit Dashboard for Real-Time Training Visualization
Shows spectral UI for each fingerprint + training process
"""

import streamlit as st
import sys
import os
from pathlib import Path
import json
import time
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.dirname(__file__))

from visualize_fingerprints import FingerprintVisualizer
from hybrid_trainer import HybridTrainer
from gemini_visualizer import generate_3d_visualization_code, execute_visualization_code, load_training_data_for_context

# Load env
env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(env_path)

st.set_page_config(
    page_title="Type Beat Training Dashboard",
    page_icon="🎵",
    layout="wide"
)

# Initialize
visualizer = FingerprintVisualizer()

st.title("🎵 Type Beat Training Dashboard")
st.markdown("**Real-time fingerprint visualization & training progress**")

# Sidebar
st.sidebar.header("⚙️ Configuration")
artists_input = st.sidebar.text_input(
    "Artists (comma-seplit)",
    value="Drake, Travis Scott, Metro Boomin"
)
max_items = st.sidebar.slider("Items per artist", 1, 50, 10)
use_spotify = st.sidebar.checkbox("Use Spotify (if available)", value=True)

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🚀 Live Training",
    "📊 Training Summary",
    "🔍 Fingerprint Explorer",
    "📈 Statistics",
    "✨ Gemini 3D Generator",
    "🔍 Discover Trending Artists"
])

with tab1:
    st.header("Live Training Monitor")
    
    if st.button("▶️ Start Training", type="primary"):
        artists = [a.strip() for a in artists_input.split(",")]
        
        # Initialize trainer
        spotify_id = os.getenv("SPOTIFY_CLIENT_ID") if use_spotify else None
        spotify_secret = os.getenv("SPOTIFY_CLIENT_SECRET") if use_spotify else None
        
        trainer = HybridTrainer(spotify_id, spotify_secret)
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        current_artist = st.empty()
        current_track = st.empty()
        spectrogram_placeholder = st.empty()
        
        total_artists = len(artists)
        total_fingerprints = 0
        
        for idx, artist in enumerate(artists):
            current_artist.markdown(f"### 🎤 Processing: **{artist}**")
            
            # Train artist
            count = trainer.train_artist_hybrid(artist, max_items)
            total_fingerprints += count
            
            # Update progress
            progress = (idx + 1) / total_artists
            progress_bar.progress(progress)
            status_text.markdown(
                f"**Progress:** {idx + 1}/{total_artists} artists | "
                f"**Fingerprints:** {total_fingerprints} total"
            )
            
            # Show latest fingerprint visualization if available
            if trainer.training_data:
                latest = trainer.training_data[-1]
                fp_vector = np.array(latest['fingerprint'])
                img = visualizer.visualize_embedding_vector(
                    fp_vector,
                    title=f"{latest.get('track_name', 'Latest')} - {artist}"
                )
                if img:
                    spectrogram_placeholder.image(img, use_container_width=True)
        
        # Save
        trainer.save_training_data("final_training_data.json")
        
        st.success(f"✅ Training complete! Generated {total_fingerprints} fingerprints")
        st.balloons()

with tab2:
    st.header("Training Data Summary")
    
    # Load latest training data
    data_path = Path("data/training_fingerprints/final_training_data.json")
    
    if data_path.exists():
        with open(data_path, 'r') as f:
            training_data = json.load(f)
        
        st.metric("Total Fingerprints", len(training_data))
        
        # Generate visualizations
        if st.button("🔄 Generate Visualizations"):
            with st.spinner("Generating visualizations..."):
                visualizations = visualizer.create_training_summary(training_data)
                
                # Display
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'artist_counts' in visualizations:
                        st.image(visualizations['artist_counts'], 
                                caption="Fingerprints per Artist")
                
                with col2:
                    if 'source_breakdown' in visualizations:
                        st.image(visualizations['source_breakdown'],
                                caption="Data Source Breakdown")
                
                if 'sample_fingerprint' in visualizations:
                    st.image(visualizations['sample_fingerprint'],
                            caption="Sample Fingerprint Vector (128-dim)")
                
                if 'embedding_space' in visualizations:
                    st.image(visualizations['embedding_space'],
                            caption="Fingerprint Embedding Space (t-SNE)")
    else:
        st.info("No training data found. Run training first!")

with tab3:
    st.header("Fingerprint Explorer")
    
    data_path = Path("data/training_fingerprints/final_training_data.json")
    
    if data_path.exists():
        with open(data_path, 'r') as f:
            training_data = json.load(f)
        
        # Select fingerprint
        track_names = [f"{item.get('track_name', 'Unknown')} - {item.get('artist', 'Unknown')}" 
                      for item in training_data]
        
        selected_idx = st.selectbox("Select Fingerprint", range(len(track_names)),
                                   format_func=lambda x: track_names[x])
        
        if selected_idx is not None:
            selected = training_data[selected_idx]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Metadata")
                st.json({
                    "Artist": selected.get('artist'),
                    "Track": selected.get('track_name'),
                    "Source": selected.get('source'),
                    "Timestamp": selected.get('timestamp')
                })
            
            with col2:
                st.subheader("Fingerprint Vector")
                fp_vector = np.array(selected['fingerprint'])
                img = visualizer.visualize_embedding_vector(
                    fp_vector,
                    title=f"{selected.get('track_name')} - {selected.get('artist')}"
                )
                if img:
                    st.image(img, use_container_width=True)
    else:
        st.info("No training data found. Run training first!")

with tab4:
    st.header("Training Statistics")
    
    data_path = Path("data/training_fingerprints/final_training_data.json")
    
    if data_path.exists():
        with open(data_path, 'r') as f:
            training_data = json.load(f)
        
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Fingerprints", len(training_data))
        
        with col2:
            artists = set(item.get('artist') for item in training_data)
            st.metric("Unique Artists", len(artists))
        
        with col3:
            youtube_count = sum(1 for item in training_data 
                              if item.get('source') == 'youtube_download')
            st.metric("From YouTube", youtube_count)
        
        with col4:
            spotify_count = sum(1 for item in training_data 
                              if item.get('source') == 'spotify_streaming')
            st.metric("From Spotify", spotify_count)
        
        # Artist breakdown table
        st.subheader("Breakdown by Artist")
        artist_counts = {}
        for item in training_data:
            artist = item.get('artist', 'Unknown')
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
        
        import pandas as pd
        df = pd.DataFrame([
            {"Artist": artist, "Fingerprints": count}
            for artist, count in sorted(artist_counts.items(), 
                                     key=lambda x: x[1], reverse=True)
        ])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No training data found. Run training first!")

with tab5:
    st.header("✨ Gemini-Powered 3D Visualization Generator")
    st.markdown("**Generate interactive 3D visualizations using Google Gemini AI**")
    
    # Check API key
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        st.error("⚠️ GEMINI_API_KEY not found in environment. Please add it to backend/.env")
        st.markdown("**📖 See `GEMINI_API_SETUP.md` for setup instructions**")
        st.stop()
    
    # Show available models
    try:
        from gemini_visualizer import get_available_models, get_best_model
        available_models = get_available_models()
        best_model = get_best_model()
        
        if available_models:
            st.info(f"✅ Using model: **{best_model}** | Available: {', '.join(available_models[:3])}")
        else:
            st.warning("⚠️ Could not detect available models. Make sure your API key has model access enabled.")
    except Exception as e:
        st.warning(f"⚠️ Could not check available models: {str(e)}")
    
    # Load training data for context
    data_path = Path("data/training_fingerprints/final_training_data.json")
    has_data = data_path.exists()
    
    if has_data:
        with st.spinner("Loading training data..."):
            data_context = load_training_data_for_context(str(data_path))
        st.success(f"✅ Loaded {len(data_context['fingerprints'])} fingerprints for context")
    else:
        data_context = None
        st.warning("⚠️ No training data found. You can still generate visualizations, but they won't use your actual data.")
    
    # Prompt input
    st.subheader("📝 Describe Your Visualization")
    
    example_prompts = [
        "Create a 3D scatter plot of audio fingerprint embeddings after PCA reduction, colored by artist",
        "Generate a 3D surface plot of a mel-spectrogram showing time, frequency, and magnitude",
        "Make an interactive 3D scatter plot using t-SNE to visualize fingerprint clusters",
        "Create a 3D bar chart comparing fingerprint counts across different artists"
    ]
    
    selected_example = st.selectbox("Or choose an example prompt:", 
                                   ["Custom..."] + example_prompts)
    
    if selected_example == "Custom...":
        user_prompt = st.text_area(
            "Enter your visualization request:",
            height=100,
            placeholder="e.g., Create a 3D scatter plot of audio fingerprint embeddings colored by artist with hover tooltips showing track names"
        )
    else:
        user_prompt = selected_example
        st.text_area("Your prompt:", value=user_prompt, height=50, disabled=True)
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        show_code = st.checkbox("Show generated code", value=True)
        auto_execute = st.checkbox("Auto-execute after generation", value=True)
    
    # Generate button
    if st.button("🚀 Generate 3D Visualization", type="primary", disabled=not user_prompt):
        if not user_prompt.strip():
            st.warning("Please enter a visualization prompt!")
        else:
            with st.spinner("🤖 Gemini is generating your 3D visualization code..."):
                try:
                    # Generate code
                    generated_code = generate_3d_visualization_code(
                        user_prompt,
                        context=data_context
                    )
                    
                    st.success("✅ Code generated successfully!")
                    
                    # Show code if requested
                    if show_code:
                        st.subheader("📄 Generated Code")
                        st.code(generated_code, language="python")
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Code",
                            data=generated_code,
                            file_name="generated_visualization.py",
                            mime="text/python"
                        )
                    
                    # Execute if requested
                    if auto_execute:
                        st.subheader("🎨 Visualization")
                        with st.spinner("Executing code and rendering visualization..."):
                            result = execute_visualization_code(generated_code, data_context)
                            
                            if result['success']:
                                st.plotly_chart(result['figure'], use_container_width=True)
                                st.success("✅ Visualization rendered successfully!")
                            else:
                                st.error(f"❌ Error executing code: {result['error']}")
                                st.info("💡 Try adjusting your prompt or check the generated code above.")
                    
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ Error generating code: {error_msg}")
                    
                    # Specific error handling
                    if "504" in error_msg or "timeout" in error_msg.lower():
                        st.warning("⏱️ **Request timed out.** This can happen if:")
                        st.markdown("""
                        - The prompt is too complex
                        - Gemini API is experiencing high load
                        - Network connection is slow
                        
                        **Try:**
                        1. Simplify your prompt
                        2. Wait a moment and try again
                        3. Use a shorter, more specific request
                        """)
                    elif "429" in error_msg or "rate limit" in error_msg.lower():
                        st.warning("🚦 **Rate limit exceeded.** Please wait a few minutes and try again.")
                    else:
                        st.info("💡 Make sure your GEMINI_API_KEY is valid and you have internet connection.")
    
    # Tips section
    with st.expander("💡 Tips for Best Results"):
        st.markdown("""
        **Good prompts include:**
        - ✅ Specific visualization type (scatter, surface, bar chart)
        - ✅ Data description (fingerprints, embeddings, spectrograms)
        - ✅ Desired features (colors, hover tooltips, interactivity)
        - ✅ Library preference (Plotly recommended)
        
        **Example prompts:**
        - "Create a 3D scatter plot of audio fingerprint embeddings after PCA reduction, colored by artist name"
        - "Generate a 3D surface plot of a mel-spectrogram with time on X-axis, frequency on Y-axis, magnitude as height"
        - "Make an interactive 3D visualization of fingerprint clusters using t-SNE, with different colors for each artist"
        
        **After generation:**
        - Review the generated code
        - Adjust if needed and re-generate
        - Download the code for later use
        - Integrate into your own scripts
        """)

with tab6:
    st.header("🔍 Discover Trending Type Beat Artists")
    st.markdown("**Find the top artists people are searching for type beats** (like BeatStars)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        max_artists = st.slider("Number of artists to discover", 10, 200, 100)
        top_display = st.slider("Top N to display", 10, 100, 50)
    
    with col2:
        auto_save = st.checkbox("Auto-save results", value=True)
        use_youtube_api = st.checkbox("Use YouTube API (faster)", value=True)
    
    if st.button("🔍 Discover Trending Artists", type="primary"):
        with st.spinner("🔍 Analyzing YouTube search results to find trending artists..."):
            try:
                from discover_trending_artists import TrendingArtistDiscoverer
                
                discoverer = TrendingArtistDiscoverer()
                
                # Override API preference if needed
                if not use_youtube_api:
                    discoverer.youtube_api_key = None
                
                artists = discoverer.discover_trending_artists(max_artists=max_artists)
                
                if artists:
                    st.success(f"✅ Discovered {len(artists)} trending artists!")
                    
                    # Display results
                    st.subheader(f"📊 Top {top_display} Trending Artists")
                    
                    # Create DataFrame for display
                    import pandas as pd
                    df_data = []
                    for i, (artist, count, data) in enumerate(artists[:top_display], 1):
                        df_data.append({
                            'Rank': i,
                            'Artist': artist,
                            'Type Beats Found': count,
                            'Total Views': f"{data['total_views']:,}",
                            'Avg Views': f"{data['avg_views']:,}",
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Show sample videos for top artist
                    if artists:
                        top_artist, top_count, top_data = artists[0]
                        with st.expander(f"🎵 Sample videos for #1: {top_artist}"):
                            for video in top_data.get('sample_videos', [])[:5]:
                                st.markdown(f"**{video['title']}**")
                                st.markdown(f"Views: {video['views']:,} | [Watch]({video['url']})")
                                st.markdown("---")
                    
                    # Save results
                    if auto_save:
                        output_path = discoverer.save_results(artists)
                        st.info(f"💾 Results saved to: `{output_path}`")
                        
                        # Download button
                        with open(output_path, 'r') as f:
                            st.download_button(
                                label="📥 Download JSON Results",
                                data=f.read(),
                                file_name="trending_artists.json",
                                mime="application/json"
                            )
                    
                    # Quick training option
                    st.subheader("🚀 Quick Actions")
                    top_artists_list = [artist for artist, _, _ in artists[:20]]
                    selected_artists = st.multiselect(
                        "Select artists to train on:",
                        top_artists_list,
                        default=top_artists_list[:5]
                    )
                    
                    if st.button("▶️ Train on Selected Artists") and selected_artists:
                        st.info(f"💡 Go to '🚀 Live Training' tab and paste: {', '.join(selected_artists)}")
                else:
                    st.warning("⚠️ No artists found. Try again or check your YouTube API key.")
                    
            except Exception as e:
                st.error(f"❌ Error discovering artists: {str(e)}")
                st.info("💡 Make sure you have yt-dlp installed: `pip install yt-dlp`")
    
    # Show saved results if available
    saved_results = Path("data/trending_artists.json")
    if saved_results.exists():
        with st.expander("📁 Previously Discovered Artists"):
            try:
                with open(saved_results, 'r') as f:
                    prev_data = json.load(f)
                
                st.metric("Total Artists", prev_data.get('total_artists', 0))
                st.caption(f"Discovered: {time.strftime('%Y-%m-%d %H:%M', time.localtime(prev_data.get('discovered_at', 0)))}")
                
                prev_artists = prev_data.get('artists', [])[:20]
                for artist_data in prev_artists:
                    st.markdown(f"**{artist_data['name']}** - {artist_data['type_beat_count']} type beats found")
            except:
                pass
