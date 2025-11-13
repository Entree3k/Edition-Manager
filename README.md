<img width="4786" height="1024" alt="Edition Manager Logo" src="https://github.com/user-attachments/assets/4b6354d2-b580-4166-8df5-18efdcade733" />

**Edition Manager** is a powerful utility that automatically generates and updates **Edition metadata** for your Plex movie library — turning your collection into a rich, visually consistent database of detailed technical and content information.
 
- **[Editions](https://support.plex.tv/articles/multiple-editions/)** — labels like *Director’s Cut*, *4K Dolby Vision*, or *Criterion Edition*.

Edition Manager leverages **Editions** to display precise and customizable metadata directly under your movie titles.

[![Buy me a slice of pizza](https://i.imgur.com/eFZcvUq.png)](https://www.buymeacoffee.com/Entree)

## Key Features

- **Automated Metadata Generation**  
  Extracts and displays information such as resolution, codecs, content ratings, HDR formats, and more.
  
- **Customizable Modular System**  
  Choose which details appear (and in what order) using the modular configuration system.

- **User-Friendly GUI**  
  Launch the included PySide6-based GUI for progress tracking, batch processing, and instant feedback.

- **Optimized Performance**  
  Multi-threaded processing, batching, and session caching for fast, efficient library updates.

- **Backup & Restore**  
  Backup edition titles before processing — and restore them anytime with a single command.

- **Seamless Plex Integration**  
  Directly communicates with your Plex server through its API to read and write metadata.

## Supported Modules

Each module extracts a specific piece of metadata and contributes it to your Plex Edition label.

| Module | Description | Example Output |
|--------|-------------|----------------|
| AudioChannels | Audio channel layout | `5.1`, `7.1` |
| AudioCodec | Audio codec | `Dolby TrueHD`, `DTS-HD MA` |
| Bitrate | Video bitrate | `24.5 Mbps` |
| ContentRating | Age rating | `PG-13`, `R` |
| Country | Production country | `United States`, `France` |
| Cut | Special cut | `Director’s Cut`, `Extended Edition` |
| Director | Film director | `Steven Spielberg` |
| Duration | Runtime | `2h 14m` |
| DynamicRange | HDR format | `Dolby Vision`, `HDR10+` |
| FrameRate | Frame rate | `24fps`, `60fps` |
| Genre | Primary genre | `Drama`, `Sci-Fi` |
| Language | Audio language | `English`, `Japanese` |
| Rating | IMDb / Rotten Tomatoes | `8.4`, `92%` |
| Release | Special release | `Criterion Edition`, `Anniversary Edition` |
| Resolution | Video resolution | `1080p`, `4K` |
| Size | File size | `58.2 GB` |
| Source | Media source | `BluRay`, `Web-DL`, `Remux` |
| SpecialFeatures | Bonus content | `Special Features` |
| Studio | Production studio | `Warner Bros.` |
| VideoCodec | Video format | `H.264`, `H.265` |

[Full Module Reference](https://github.com/Entree3k/Edition-Manager/blob/main/Edition%20Manager%20Modules.md)

## GUI Usage

<img width="652.6666666666667" height="498.6666666666667" alt="edition_manager" src="https://github.com/user-attachments/assets/8a0b22ae-66ba-45d8-921b-41764e8b34e0" />

Edition Manager includes a full-featured desktop [GUI](https://github.com/Entree3k/Edition-Manager/blob/main/Edition%20Manager%20GUI.md).
```bash
python edition_manager_gui.py
```
> 💡 On Windows, you can double-click `edition_manager_gui.pyw` to launch it directly.

The GUI supports:

-   All or single-movie processing
    
-   Batch progress tracking
    
-   Backup and restore tools
    
-   Configuration editor with visual module ordering
    
-   Optional webhook server for automatic processing when new movies are added


## Command Line Usage

Edition Manager also supports CLI mode for advanced or automated workflows:

Process all movies `python edition_manager.py --all`

Process one movie `python edition_manager.py --one`

Clear all Edition data `python edition_manager.py --reset`

Backup Edition metadata `python edition_manager.py --backup`

Restore metadata from backup `python edition_manager.py --restore`

Restore from a specific file `python edition_manager.py --restore-file <file_name>`

List available backups `python edition_manager.py --list-backups`

## Configuration

Edit the `config/config.ini` file to customize Edition Manager.

### [server]

`address` - Your Plex server URL (e.g., `http://localhost:32400`)

`token` - Your Plex authentication token

`skip_libraries` - Libraries to exclude (semicolon-separated)

### [modules]

`order` - Module order, separated by semicolons (e.g., `Resolution;AudioCodec;Bitrate`)

### [language]

`excluded_languages` - Languages to ignore

`skip_multiple_audio_tracks` - Skip tagging when multiple audio tracks exist

### [rating]

`source` - Choose `imdb` or `rotten_tomatoes`

`rotten_tomatoes_type` - `critic` or `audience`

`tmdb_api_key` - Required for IMDb lookups via TMDb

### [performance]

`max_workers` - Number of concurrent threads

`batch_size` - Movies processed per batch

## Previews

Different module combinations yield unique Edition styles:

![Cut Release](https://github.com/x1ao4/edition-manager-for-plex/assets/112841659/28047dfe-a058-4cf3-8a32-ca8882edae15)

`order = Cut;Release`

![Rating Country](https://github.com/x1ao4/edition-manager-for-plex/assets/112841659/05214007-f2ed-423e-82a3-188712933446)

`order = Rating;Country`

![Resolution AudioCodec](https://github.com/x1ao4/edition-manager-for-plex/assets/112841659/97606ea4-e5e0-45e4-8633-08f77181ef96)

`order = Resolution;AudioCodec`

![Multi-module](https://github.com/x1ao4/edition-manager-for-plex/assets/112841659/11ca5070-1757-4790-a896-5da97ce976a9)

`order = Release;Source;Resolution;DynamicRange;VideoCodec;FrameRate;AudioCodec;Bitrate;Size;Country`

## Requirements

-   Python **3.10+**
    
-   Dependencies installed via:
    
    ```bash
    pip install -r requirements.txt
    ```
    
-   Plex Media Server running and accessible


## Troubleshooting

### Common Issues

**1. Connection Errors**

-   Ensure Plex is running and reachable
    
-   Verify `address` and `token` in `config.ini`

**2. No Metadata Appearing**

-   Confirm enabled modules in the config
    
-   Check movie filenames follow common naming conventions
    
-   Review logs for module-specific errors

**3. Performance**

-   Reduce `max_workers` for older CPUs
    
-   Lower `batch_size` for better responsiveness

**4. Language Detection**

-   Use [MKVToolNix](https://mkvtoolnix.download/) (Manual) or [ULDAS](https://github.com/netplexflix/ULDAS) (Automated) to correct track language metadata

## Contributing

Contributions are welcome!  
Submit issues or pull requests for new modules, bug fixes, or improvements.

## License

This project is licensed under the **MIT License**.

## Acknowledgements

All respect to [x1ao4](https://github.com/x1ao4) for the original foundation.

## Support

If you enjoy Edition Manager, please consider giving it a **⭐ on GitHub**  
or [buying me a slice of pizza 🍕](https://www.buymeacoffee.com/Entree).  

Your support helps keep development going!
