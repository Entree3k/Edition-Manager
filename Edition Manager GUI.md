
# Edition Manager GUI - User Guide

This is just a basic guide on how to use the Edition Manager GUI

## What the app does

Edition Manager scans your Plex movie libraries and writes a smart **Edition Title** built from metadata (e.g., cut, resolution, dynamic range, audio codec, language, boutique label, rating, etc.). You can run it on all movies, a single movie, or restore/undo changes using the built‑in backup tools.

## Quick start

1.  **Open Settings** (top right of the main window)
    
2.  Enter your **Plex Server URL** (e.g., `http://127.0.0.1:32400`) and **Token**
    
3.  Click **Test Connection**. If successful, optionally use **Library Picker** to skip whole libraries
    
5.  Visit the **Modules** tab to reorder/enable the tags you want in the Edition Title
    
6.  (Optional) Tune **Language**, **Rating**, **Performance**, and **Appearance**
    
7.  Click **Save**
    
8.  Back on the main screen, choose an action: **Process All Movies**, **Process One Movie**, **Reset All Movies**, **Backup Editions**, or **Restore Editions**

## Main window

<img width="652.6666666666667" height="498.6666666666667" alt="edition_manager" src="https://github.com/user-attachments/assets/8a0b22ae-66ba-45d8-921b-41764e8b34e0" />

-   **Actions**
    
    -   **Process All Movies**: Run Edition Manager on every movie in un‑skipped libraries
        
    -   **Process One Movie**: Opens a poster grid with results (title/year/library); double‑click a match to process that item only
        
    -   **Reset All Movies**: Clears the Edition Title for all processed movies
        
    -   **Backup Editions**: Saves current titles to a JSON file for safekeeping
        
    -   **Restore Editions**: Restores titles from a prior backup
        
    -   **Settings**: Opens the configuration dialog
        
-   **Progress**
    
    -   Shows a busy indicator while work is running, then a percentage and completion status
        
-   **Status Log**
    
    -   Real‑time output from the engine. Use **Cancel** to stop the current task, or **Clear Status** to wipe the log view

## Settings

<img width="478.6666666666667" height="392" alt="settings" src="https://github.com/user-attachments/assets/f938cbfc-5bd9-4197-81d0-ae5b8549fbe1" />

Settings are organized into tabs. All changes are saved to a `config.ini` in the app’s `config/` folder when you click **Save**

### Server

-   **Server URL** - Your Plex HTTP URL
    
-   **Token** - Plex token with library read/write permissions
    
-   **Skip Libraries** - Semicolon‑separated list. Click **Library Picker…** to select movie libraries to skip
    
-   **Webhook (toggle)** - When enabled, the GUI starts a minimal webhook server so _newly added movies_ can be auto‑processed
    
-   **Tools** — **Test Connection** checks reachability and lists sections; **Library Picker…** helps build the skip list

### Modules

<img width="478.6666666666667" height="392.6666666666667" alt="modules" src="https://github.com/user-attachments/assets/6a9d39f2-ac8a-43c1-8023-63ae383a34c0" />

-   **Drag to reorder**; **check to enable**. Enabled modules run top‑to‑bottom and compose the Edition Title in that order.
    
-   Modules include: AudioChannels, AudioCodec, Bitrate, ContentRating, Country, Cut, Director, Duration, DynamicRange, FrameRate, Genre, Language, Rating, Release, Resolution, ShortFilm, Size, Source, SpecialFeatures, Studio, VideoCodec, Writer

### Language

<img width="480" height="392.6666666666667" alt="language" src="https://github.com/user-attachments/assets/27fff059-bb2e-4bb4-b475-ea0ceec8f224" />

-   **Excluded Languages** — Comma‑separated list; any matching audio track languages will be ignored when selecting a primary language tag.
    
-   **Skip Multiple Audio Tracks** — If checked, movies with more than one audio track are skipped by the Language module to avoid ambiguity.
    

### Rating

<img width="478.6666666666667" height="390.6666666666667" alt="rating" src="https://github.com/user-attachments/assets/ae63c8b8-e9f6-4b81-94bd-1de4a30cf1a2" />

-   **Source** — Choose **IMDB** (via TMDb) or **Rotten Tomatoes**
    
-   **Rotten Tomatoes Type** — **Critics** or **Audience** (only used when source is Rotten Tomatoes)
    
-   **TMDb API Key** — Required for IMDB source  

### Performance

<img width="478.6666666666667" height="390.6666666666667" alt="performance" src="https://github.com/user-attachments/assets/96d43924-de65-44f7-ae24-bccdcb795566" />

-   **Hardware** — Shows detected CPU threads

-   **Library Size** — Small / Medium / Large presets
    
-   **Apply Recommendation** — Fills in optimized **Max Workers** and **Batch Size** based on CPU and chosen size
    
-   **Max Workers** — Parallel movies processed at once
-   **Batch Size** — Movies per round before reporting progress

### Appearance

<img width="478.6666666666667" height="390.6666666666667" alt="appearance" src="https://github.com/user-attachments/assets/04c1753f-971c-4b0d-a5cc-826d8bc06f15" />

-   **Primary Highlight Color** — Pick a brand color for buttons, progress, and accents
-   **Dark Mode** — Toggle a dark UI theme.

## Webhook auto‑processing (optional)

When **Webhook** is enabled in Settings, the GUI launches a small local server. Wire your Plex **webhook** to POST new‑item events to the app. The GUI filters duplicates and stale events and queues the movie for processing in the background. A minimal health endpoint is also available.

-   Health: `GET /healthz` → `{ "ok": true }`
    
-   Webhook target: `POST /edition-manager` with Plex payload

> Tip: Only **movie** `library.new` events added within a few minutes are processed. This prevents spam and old replays.

## How to set up the Webhook in Plex

1.  **Enable the Webhook Server in Edition Manager:**
    
    -   Go to **Settings → Server** and toggle **Webhook** ON.
        
    -   Note the server address shown in the log, e.g. `http://<your-local-ip>:5000/edition-manager`.
        - `<your-local-ip>` is the IP of the device running the Script
2.  **Open Plex Settings:**
    
    -   In Plex Web, click the **Settings** icon → **Server** → **Webhooks**
        
3.  **Add the Edition Manager webhook:**
    
    -   Click **Add Webhook** and paste your Edition Manager endpoint URL (for example, `http://<your-local-ip>:5000/edition-manager`).
        
    -   Click **Save Changes.**
        
4.  **Test the Webhook:**
    
    -   Add a new movie to Plex.
    -   In Edition Manager, check the **Status Log** — you should see an entry like:

   ```
   [Webhook] Received new movie event: Inception (2010)
   [Webhook] Queued for automatic processing.
   ```
        
5.  **Check Health Endpoint:**
    
    -   Visit `http://<your-local-ip>:5000/healthz` in your browser. You should see:

        ```json
        { "ok": true }
        ```
        
6.  Edition Manager will now automatically process any newly added movies as they appear in your Plex library.

## How Edition Titles are built

Each enabled module returns a short, human‑readable tag (when available). The tags are de‑duplicated and joined with `·` to form the final Edition Title. Examples:

-   `Dolby Vision · HDR10 · 4K · 5.1 · DTS‑HD MA · Director's Cut`
    
-   `1080p · AAC · 24fps · French · Criterion`
    

If a module can’t determine a value for a movie, it simply contributes nothing for that movie.

## Tips & good practices

-   **Backup before large runs** with **Backup Editions** so you can undo easily.
    
-   **Start small**: test with **Process One Movie** to confirm the title format before running on your entire library.
    
-   **Prioritize signal**: Put your favorite tags (e.g., **Release** boutique labels or **DynamicRange**) at the top of the Modules list.
    
-   **Language clarity**: Add your native language to **Excluded Languages** if you prefer Edition Titles to only highlight non‑native tracks.
    
-   **Ratings**: If you choose **Rotten Tomatoes**, set **Critics** or **Audience** to match your preference; for IMDB, add a TMDb API key.
    
-   **Performance**: Use **Apply Recommendation** first; adjust **Max Workers** up/down if your Plex server is busy with other tasks.
    
-   **Appearance**: Pick a primary color that contrasts well in your theme; enable **Dark Mode** if you usually run Plex at night.

## Troubleshooting

-   **Connection failed** in Settings → Server
    
    -   Verify URL, token, and network; confirm Plex responds at `/library/sections`.
        
-   **No posters in search** (Process One Movie)
    
    -   Ensure the GUI can reach your Plex server and the token has access to library images.
        
-   **Nothing happens on new items** (Webhook)
    
    -   Confirm the **Webhook** toggle is on and check Health Endpoint
        
-   **Edition Titles look wrong**
    
    -   Re‑order modules so the most important tags appear first; disable modules you don’t need. Then **Reset All Movies** and re‑run.
