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
## 注意事项
- 请确保你提供了正确的 Plex 服务器地址和正确的 X-Plex-Token。
- 请确保你提供了正确的库名，并按要求进行了填写。
- 请确保你按照要求设置了正确的语言和模块信息。
- 如果脚本无法连接到 Plex 服务器，请检查你的网络连接，并确保服务器可以访问。
- 请使用服务器管理员账号的 X-Plex-Token 运行脚本，以确保你拥有足够的权限进行操作。
- 版本信息将在添加后被锁定，若有修改需求，Plex Pass 订阅用户可以手动解锁版本信息，然后进行修改；非 Plex Pass 订阅用户不支持手动修改版本信息。若要为所有电影修改版本信息的模块或排序，请先重置版本信息，然后修改配置文件，再重新写入版本信息。
- 修改配置文件后，需要重启容器，新的配置信息才会生效。
- Windows 用户运行 Python 脚本后，若没有任何反应，请将运行命令或启动脚本中的 `python3` 替换为 `python` 再运行。

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
### Bitrate
The Bitrate module retrieves the bitrate information of video files from the media metadata recognized by Plex. If multiple video files exist, it retrieves the bitrate information from the largest file by size. If bitrate information cannot be found, it will not write any bitrate information (bitrate units are in Kbps, Mbps).

### Size
The Size module retrieves the size information of video files from the media metadata. If multiple video files exist, it retrieves the size information from the largest file by size (size units are in B, KB, MB, GB).

### Country
The Country module retrieves the country (or region) information of movies from the movie metadata. If multiple countries exist, it sequentially writes the country information. If country information cannot be found, it will not write any country information.

### ContentRating
The ContentRating module retrieves the content rating information of movies from the movie metadata. If content rating information cannot be found, it will not write any content rating information. Supported content ratings include but are not limited to:

#### Movie Ratings (MPAA)
- **G**: General Audiences – Suitable for all ages. Contains nothing that would offend parents for viewing by children.
- **PG**: Parental Guidance Suggested – Some material may not be suitable for children. Parents are urged to give "parental guidance."
- **PG-13**: Parents Strongly Cautioned – Some material may be inappropriate for children under 13. Parents are urged to be cautious.
- **R**: Restricted – Restricted to viewers over the age of 17 or accompanied by a parent or adult guardian. Contains strong language, violence, or sexual content.
- **NC-17**: Adults Only – No one 17 and under admitted. Contains explicit sexual or violent content.
- **NR**: Not Rated – The film has not been submitted for rating to the MPAA.
- **Unrated**: A version not officially rated by organizations like the MPAA, may contain content not included in the original rating.

#### TV Show Ratings (TV Parental Guidelines)
- **TV-Y**: Television for All Children – Suitable for all children. Typically suitable for ages 2-6.
- **TV-Y7**: Directed to Older Children – Suitable for children age 7 and above. May contain mild fantasy violence or infrequent use of mild language.
- **TV-Y7-FV**: Directed to Older Children - Fantasy Violence – Suitable for children age 7 and above. Contains fantasy violence.
- **TV-G**: General Audience – Suitable for all ages. Contains little or no violence, no strong language, and little or no sexual dialogue or situations.
- **TV-PG**: Parental Guidance Suggested – Some material may not be suitable for children. Parents are urged to provide "parental guidance."
- **TV-14**: Parents Strongly Cautioned – Contains some material that many parents would find unsuitable for children under 14.
- **TV-MA**: Mature Audience Only – This program is specifically designed to be viewed by adults and may be unsuitable for children under 17. May contain crude indecent language, explicit sexual activity, or graphic violence.

#### Other Rating Standards
- **Approved**: Approved by the Motion Picture Association or other relevant authorities. Suitable for public viewing, specific content may vary depending on release era.
- **18+**: Restricted to viewers 18 years and older. Contains adult-oriented content.
- **AO**: Adults Only – Used for video game ratings, suitable only for adults.

Note: The above ratings are based on the U.S. rating system. Ratings systems in other regions may vary.

### Rating
The Rating module retrieves the audience rating information of movies from the movie metadata (using the configured rating source from the database). If rating information cannot be found, it will not write any rating information (ratings will be converted to a 10-point scale).

### Duration
The Duration module retrieves the duration information of video files from the media metadata of movies. If multiple video files exist, it retrieves the duration information from the largest file by size. If duration information cannot be found, it will not write any duration information (duration is measured in minutes).

## Features
The EMP operates in three modes: `add editions for all movies (all)`, `add editions for new movies (new)`, and `reset editions for all movies (reset)`:

- **add editions for all movies**: Based on user configuration, this mode adds editions for all movies in libraries excluding those configured to be skipped. Movies with existing editions will be skipped.
- **add editions for new movies**: This mode utilizes Webhooks to listen for server events in real-time, capturing metadata for newly added items. It then adds editions only for newly added movies (excluding those in libraries configured to be skipped).
- **reset editions for all movies**: According to user settings, this mode resets (removes) editions for all movies in libraries excluding those configured to be skipped.

Note: The `add editions for new movies` mode requires the server administrator account to be subscribed to Plex Pass in order to use.

## Config
Before using EMP, please configure `/config/config.ini` according to the following example:
```
[server]
# Address of the Plex server, formatted as http://server IP address:32400 or http(s)://domain:port
address = http://127.0.0.1:32400
# Token of the Plex server for authentication
token = xxxxxxxxxxxxxxxxxxxx
# Specify libraries to skip, format should be LibraryName1;LibraryName2;LibraryName3, leave empty if no libraries need to be skipped
skip_libraries = Cloud Movie;Concert
# Language setting, 'zh' for Chinese, 'en' for English
language = en

[modules]
# Specify modules to write and their order, format should be Module1;Module2;Module3, optional modules include Cut, Release, Source, Resolution, DynamicRange, VideoCodec, FrameRate, AudioCodec, Bitrate, Size, Country, ContentRating, Rating, Duration
order = Source;DynamicRange
```
Since EMP only processes libraries of movie type, specify libraries of movie type to skip when needed. There is no limit to the number of modules for writing editions, so you can choose and configure them according to your needs.

When running in `add editions for new movies` mode, EMP creates a Flask web server that listens on port `8089` to receive `library.new` events sent by the Plex server. This allows it to capture metadata for newly added items and process them accordingly.

If port `8089` is already occupied by another service, you may need to modify the `port=8089` on the ninth last line of `edition-manager-for-plex.py` (when running via Python script) or adjust port mapping (when running via Docker container) to change the listening port.

## How to Run
You can run EMP using Docker containers or Python scripts. Docker containerization is recommended for its ease of use and scalability. Detailed instructions for each method are provided below.

### Running via Docker Container

#### Requirements
- Docker and Docker Compose installed.

#### Docker Compose
- edition-manager-for-plex (Plex Pass subscribers)
  
   ```
   version: "2"
   services:
     emp-all:
       image: x1ao4/edition-manager-for-plex:latest
       container_name: emp-all
       command: python edition-manager-for-plex.py --all
       environment:
         - TZ=Asia/Shanghai
       volumes:
         - /custom/directory/edition-manager-for-plex/config:/app/config
     emp-new:
       image: x1ao4/edition-manager-for-plex:latest
       container_name: emp-new
       command: python edition-manager-for-plex.py --new
       ports:
         - 8089:8089
       environment:
         - TZ=Asia/Shanghai
       volumes:
         - /custom/directory/edition-manager-for-plex/config:/app/config
       restart: unless-stopped
   networks: {}
   ```
- edition-manager-for-plex（Non-Plex Pass subscribers）
  
   ```
   version: "2"
   services:
     emp-scheduler:
       image: mcuadros/ofelia:latest
       container_name: emp-scheduler
       depends_on:
         - emp-all
       command: daemon --docker -f label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}
       labels:
         ofelia.job-run.emp-all.schedule: 0 30 22 * * *
         ofelia.job-run.emp-all.container: emp-all
       environment:
         - TZ=Asia/Shanghai
       volumes:
         - /var/run/docker.sock:/var/run/docker.sock:ro
       restart: unless-stopped
     emp-all:
       image: x1ao4/edition-manager-for-plex:latest
       container_name: emp-all
       command: python edition-manager-for-plex.py --all
       environment:
         - TZ=Asia/Shanghai
       volumes:
         - /custom/directory/edition-manager-for-plex/config:/app/config
   networks: {}
   ```
- edition-manager-for-plex-reset
  
   ```
   version: "2"
   services:
     emp-reset:
       image: x1ao4/edition-manager-for-plex:latest
       container_name: emp-reset
       command: python edition-manager-for-plex.py --reset
       environment:
         - TZ=Asia/Shanghai
       volumes:
         - /custom/directory/edition-manager-for-plex/config:/app/config
   networks: {}
   ```

#### Usage
With EMP, you can write edition information as well as remove it. Since Docker automatically starts all containers within the stack upon stack initialization, the functions for writing and removing need to be deployed separately. First, deploy `edition-manager-for-plex` to write edition information, then deploy `edition-manager-for-plex-reset` when needed to remove edition information (upon deployment, it will immediately execute a `reset editions for all movies` once. You can also use `docker-compose up --no-start` to deploy this container, which will not run immediately after deployment; start the container only when needed).

- edition-manager-for-plex

  1. In the Plex server settings, navigate to `Webhooks`, click on `Add Webhook`, and enter your Flask server address `http://Docker host IP address:8089` and `Save Changes`. (Non-Plex Pass subscribers do not need to fill this.)
  2. Download the `/compose/edition-manager-for-plex/compose.yaml` file from the repository (Plex Pass subscribers should delete the `emp-scheduler` section; non-Plex Pass subscribers should delete the `emp-new` section) and save it in a folder named `edition-manager-for-plex`.
  3. Open `compose.yaml` with a text editor and replace `/custom/directory/edition-manager-for-plex/config` with a directory on your host machine where configuration files will be stored. (Both `emp-all` and `emp-new` should use the same directory.)
  4. Open the terminal or command line tool, use the `cd` command to switch to the directory where `compose.yaml` is located.
  5. Use the command `docker-compose up -d` to deploy and start the edition-manager-for-plex stack.
  6. Open `/custom/directory/edition-manager-for-plex/config/config.ini` with a text editor, fill in your Plex server address (`address`) and [X-Plex-Token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) (`token`), set the modules to write edition information and their order (`order`), and optionally fill in other configuration options as needed.
  7. Restart the edition-manager-for-plex stack to start running properly.

- edition-manager-for-plex-reset

  1. Download the `/compose/edition-manager-for-plex-reset/compose.yaml` file from the repository and save it in a folder named `edition-manager-for-plex-reset`.
  2. Open `compose.yaml` with a text editor and replace `/custom/directory/edition-manager-for-plex/config` with a directory on your host machine where configuration files will be stored. (Use the same directory as `emp-all` and `emp-new`.)
  3. Open the terminal or command line tool, use the `cd` command to switch to the directory where `compose.yaml` is located.
  4. Use the command `docker-compose up -d` to deploy and start the edition-manager-for-plex-reset stack. (If `/custom/directory/edition-manager-for-plex/config/config.ini` is correctly configured, the stack will operate properly; if not configured, fill in the configuration information first, then restart the stack for proper operation.)

#### Instructions
EMP consists of four containers: `emp-all`, `emp-new`, `emp-scheduler`, and `emp-reset`, each designed to handle different tasks. Upon stack deployment, these containers will have slightly different running states.

- The `emp-all` container is used for the `add editions for all movies` task. It runs this task once after startup, processing all movies within the set scope (adding edition information), and displays the library information and processing results in the terminal or logs. It will stop running after completing the task. You can start it at any time to run the `add editions for all movies` task, and it will stop after each run. If you have configured `emp-scheduler`, `emp-all` will also run once automatically at each scheduled task time.
- The `emp-new` container is used for the `add editions for new movies` task. After startup, it will create a Flask server to listen for events from the Plex server. When there are new movies on the Plex server, it will automatically process the new movies (add edition information) and display the processing results in the terminal or logs. After processing, it will continue to listen for events from the Plex server and handle any new movies as they arrive, then resume listening.
- The `emp-scheduler` container is used to set/trigger scheduled tasks for `add editions for all movies`. After startup, it will create a scheduled task to run `emp-all` at a default setting of `0 30 22 * * *`, which means it will run once daily at 10:30 PM. You can customize the running frequency by modifying the cron expression, such as `"@every 3h"` for every 3 hours or `"@every 30m"` for every 30 minutes. It will start the `emp-all` container at the scheduled task time and synchronize the `emp-all` log information in the terminal or logs, then continue running.
- The `emp-reset` container is used for the `reset editions for all movies` task. It runs this task once after startup, processing all movies within the set scope (resetting/removing edition information), and displays the library information and processing results in the terminal or logs. It will stop running after completing the task. You can start it at any time to run the `reset editions for all movies` task, and it will stop after each run.

You can select and configure these four containers as needed. If certain functions are not required, simply delete the corresponding parts in the Compose file before deployment.

### Running via Python Script

#### Requirements
- Python 3.0 or higher installed.
- Necessary third-party libraries installed using the command `pip3 install -r requirements.txt`.

#### Usage
1. Download the latest release package from [Releases](https://github.com/x1ao4/edition-manager-for-plex/releases) and extract it to a local directory.
2. Open the `/config/config.ini` file in the directory using a text editor, fill in your Plex server address (`address`) and [X-Plex-Token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) (`token`), set the modules to write edition information and their order (`order`), and optionally fill in other configuration options as needed.
3. In the Plex server settings, navigate to `Webhooks`, click on `Add Webhook`, and enter your Flask server address `http://IP address of the device running the script:8089` and `Save Changes`. (Non-Plex Pass subscribers do not need to fill this.)
4. Open a terminal or command line tool, use the `cd` command to switch to the directory where the script is located.
5. Use the command `python3 edition-manager-for-plex.py --all` to run the `add editions for all movies` task. The script will process all movies within the configured scope (adding edition information) and display library information and processing results in the console. It will stop running after completing the task.
6. Use the command `python3 edition-manager-for-plex.py --new` to run the `add editions for new movies` task. The script will create a Flask server to listen for events from the Plex server. When there are new movies on the Plex server, the script will automatically process the new movies (adding edition information) and display the processing results in the console. After processing, it will continue to listen for events from the Plex server and handle new movies as they arrive, then resume listening.
7. Use the command `python3 edition-manager-for-plex.py --reset` to run the `reset editions for all movies` task. The script will process all movies within the configured scope (resetting/removing edition information) and display library information and processing results in the console. It will stop running after completing the task.

#### Quick Start
PC users can quickly start tasks by double-clicking the provided scripts:

- To run the `add editions for all movies` task, double-click `emp-all.bat (Win)` or `emp-all.command (Mac)`.
- To run the `add editions for new movies` task, double-click `emp-new.bat (Win)` or `emp-new.command (Mac)`.
- To run the `reset editions for all movies` task, double-click `emp-reset.bat (Win)` or `emp-reset.command (Mac)`.

#### Automation
For convenience, you can set up EMP to run automatically using crontab or other task scheduling tools.

- Add Editions for All Movies (Mac)
  
  1. Open the crontab file in the terminal with the command `crontab -e`.
  2. Press `i` to enter insert mode and add the line `30 22 * * * /path/to/emp-all.command > /dev/null 2>&1`. (Replace `/path/to/emp-all.command` with the actual path to your script.)
  3. Press `Esc` to exit insert mode, type `:wq`, and press `Enter` to save changes and exit the editor.

  This sets up a scheduled task to run the `add editions for all movies` script every day at 10:30 PM. You can customize the frequency by modifying the time expression, such as `0 */3 * * *` to run every 3 hours or `*/30 * * * *` to run every 30 minutes. (The script will run in the background.)

- Add Editions for New Movies (Mac)
  
  1. Open the `emp-new.command` file with a text editor, add `sleep 10` on the second line, save the changes, and close the file.
  2. Open the crontab file in the terminal with the command `crontab -e`.
  3. Press `i` to enter insert mode and add the line `@reboot /path/to/emp-new.command`. (Replace `/path/to/emp-new.command` with the actual path to your script.)
  4. Press `Esc` to exit insert mode, type `:wq`, and press `Enter` to save changes and exit the editor.

  This sets the `add editions for new movies` script to run on Mac startup, with a 10-second delay to ensure the Plex server starts before the script. (The script will run in the background.)

- Add Editions for All Movies (NAS)
  
  Use the built-in task scheduler to add a scheduled task for `add editions for all movies`. After adding the task, enter `python3 /path/to/edition-manager-for-plex.py --all` in the `Run Command - User-Defined Script` field, then set the desired run time. (Replace `/path/to/edition-manager-for-plex.py` with the actual path to your script.)
  
- Add Editions for New Movies (NAS)
  
  Use the built-in task scheduler to set `add editions for new movies` to run at startup. After adding the task, enter `sleep 10 && python3 /path/to/edition-manager-for-plex.py --new` in the `Run Command - User-Defined Script` field. This ensures the script runs 10 seconds after NAS startup, giving the Plex server time to start first. (Replace `/path/to/edition-manager-for-plex.py` with the actual path to your script.)

If the scripts fail to run as scheduled or on startup, you may need to replace `python3` with the full path to the Python interpreter. You can find the actual path to `python3` using the `which python3` command in the Mac terminal or NAS SSH.

## Notes
- Ensure you provide the correct Plex server address and the correct X-Plex-Token.
- Ensure you provide the correct library names and fill them in as required.
- Ensure you correctly set the language and module information as required.
- If the script cannot connect to the Plex server, check your network connection and ensure the server is accessible.
- Use the server administrator account's X-Plex-Token to run the script to ensure you have sufficient permissions for operations.
- The edition field will be locked after being added. If modifications are needed, Plex Pass subscribers can manually unlock the edition field and then modify it; non-Plex Pass subscribers do not support manual modification of the edition field. To modify the edition modules or their order for all movies, first reset the editions, then modify the configuration file, and finally rewrite the editions.
- After modifying the configuration file, you need to restart the container for the new configuration to take effect.
- If Windows users see no response after running the Python script, try replacing `python3` with `python` in the run command or start script.

## Support

If you enjoy Edition Manager, please consider giving it a **⭐ on GitHub**  
or [buying me a slice of pizza 🍕](https://www.buymeacoffee.com/Entree).  

Your support helps keep development going!
