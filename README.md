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
使用 Edition Manager for Plex（下文简称 EMP）可以自动获取电影和电影文件的信息，并将指定的信息写入 Edition 字段，从而丰富电影信息的展示功能。你可以通过 EMP 将电影的剪辑版本、发行版本、片源版本、分辨率、动态范围、视频编码、帧率、音频编码、比特率、大小、国家、内容分级、评分或时长写入电影的 Edition 字段，而且还支持自选模块和自定义排序。

这一切都将通过 EMP 自动实现，无需编辑或修改文件名。这意味着你不需要在文件名中按照 `{edition-Edition Title}` 这样的格式添加版本信息，EMP 会通过文件名或电影的元数据自动查找相关的信息，然后将需要的信息写入 Edition 字段，对文件的命名没有特殊要求。

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
In Plex, there are two concepts of "version": "[Edition](https://support.plex.tv/articles/multiple-editions/)" and "[Version](https://support.plex.tv/articles/200381043-multi-version-movies/)", but their uses are quite different.

The primary design of Edition is to differentiate between various cut versions of a film, such as Theatrical Cut, Director's Cut, Extended Cut, Unrated Cut, etc. If you have different cut versions of the same movie, you can label and distinguish them by editing the Edition in Plex. These different versions will be displayed as separate entries in the media library, each with its own viewing status, progress, and rating records, independent of each other.

The primary design of Version is to integrate multiple file versions of the same cut, mainly referring to different resolutions, encoding formats, or dynamic ranges, such as 1080P, 4K, SDR, HDR, etc. If you have different file versions of the same movie, they will automatically merge into a single entry in the media library after successful matching. You can choose which version to watch through "Play Version" during playback (if not selected, the default version will be played). They will share the same viewing status, progress, and rating records.

The Edition is displayed below the title, after the year, and also in the "More Ways to Watch/Watch From These Locations" section, and it supports custom display names. In contrast, the Version is only shown on the movie's detail page and does not support custom display names. Since the actual use cases for marking different cut versions are not frequent and the Edition's display position is quite prominent, we can fully utilize this feature to mark other information about the movie beyond just different cuts.

For instance, currently, Plex's mobile and TV apps do not display Dolby Vision information. We can achieve this by writing the dynamic range into the Edition, allowing Dolby Vision information to be displayed on mobile and TV apps. This way, we can distinguish which movies are Dolby Vision versions. Additionally, Plex's library sorting currently only supports single sorting criteria. You cannot display the movie's resolution or bitrate information while sorting by title or audience rating. Similarly, we can display this extra information through Edition.

Using Edition Manager for Plex (hereinafter referred to as EMP), you can automatically retrieve information about movies and movie files and write the specified information into the Edition field, enriching the display functionality of movie information. With EMP, you can write the movie's Cut Version, Release Version, Source Version, Resolution, Dynamic Range, Video Codec, Frame Rate, Audio Codec, Bitrate, Size, Country, Content Rating, Audience Rating, or Duration into the Edition field. It also supports custom modules and custom sorting. 

All of this will be automatically handled by EMP, without the need to edit or modify filenames. This means you don't need to add Edition information to the filename in the format `{edition-Edition Title}`. EMP will automatically search for relevant information through filenames or the movie's metadata, and then write the required details into the Edition field. There are no specific requirements for naming files.

You can use EMP to add extra display information to your movies according to your needs and preferences. We provide features for writing and removing Editions, allowing you to try any combination freely and remove all Edition information with one click at any time. Although Edition is an exclusive feature for Plex Pass, EMP allows you to use the Edition feature without a Pass subscription.

## Demo
Configuration `order = Cut;Release` looks like this:

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
