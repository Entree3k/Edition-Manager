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
配置 `order = 片源版本；动态范围` 的效果：

![片源版本 动态范围](https://github.com/x1ao4/edition-manager-for-plex/assets/112841659/2876cef3-9b3a-4cd7-a2d7-761fe1874a7e)

配置 `order = 内容分级；时长` 的效果：

![内容分级 时长](https://github.com/x1ao4/edition-manager-for-plex/assets/112841659/5d4c1917-b79c-4ec3-98f9-7e8553aa13f8)

配置 `order = 发行版本；片源版本；分辨率；动态范围；视频编码；帧率；音频编码；比特率；大小；国家` 的效果：

![多模块](https://github.com/x1ao4/edition-manager-for-plex/assets/112841659/d58815eb-c943-4b47-8783-ab7a993122f5)

## 模块
目前 EMP 共有 14 个模块可供选择，分别是剪辑版本、发行版本、片源版本、分辨率、动态范围、视频编码、帧率、音频编码、比特率、大小、国家、内容分级、评分和时长，你可以选择任意数量的模块，并按照任意顺序进行排序，若个别模块获取不到信息，其他模块也会正常显示，按照需要选配即可。

### 剪辑版本
剪辑版本模块目前支持 12 种剪辑版本，该模块会优先使用电影的文件名匹配剪辑版本信息，若存在多个视频文件，则会使用文件大小最大的视频文件进行匹配，若找不到剪辑版本信息，则会通过文件内嵌的视频标题进行匹配，若依然找不到剪辑版本信息，则不会写入剪辑版本信息。支持的剪辑版本如下：

- **院线版**：这是在电影院上映的版本，通常是最广为人知的版本。这个版本经过制片人和发行方的最终审核，以便适合大规模公映。
- **导演剪辑版**：这是导演本人认为最能体现他创作意图的版本。这个版本可能包含被删减的镜头或不同的叙事结构，通常在影院上映后发行。
- **制片人剪辑版**：由制片人主导剪辑的版本，通常与导演的意图有所不同。制片人剪辑版有时会为了商业考虑而对影片进行修改。
- **加长版**：包含了在院线版中被删减的场景或扩展了某些片段的版本。加长版通常在影片的家庭影音版中发行，提供更多内容给观众。
- **未分级版**：未经过电影分级机构审核的版本，通常包含更激烈或更有争议的内容。未分级版一般在家庭娱乐市场上发布。
- **最终剪辑版**：这是影片的最终定版，通常包含了所有创作团队的意见。最终剪辑版可能是为了庆祝电影的重要周年纪念而发布的。
- **电视版**：为电视播出而特别剪辑的版本，通常会删除或修改一些不适合电视观众观看的内容，以符合电视台的规定。
- **国际版**：针对国际市场进行调整的版本，可能会添加字幕或配音，并修改一些文化差异较大的内容。
- **家庭录像版**：为家庭观看而发布的版本，包括 VHS、DVD、蓝光等格式。家庭录像版有时会包含院线版没有的额外内容或特别花絮。
- **初剪版**：这是影片在正式剪辑完成前的初步版本，包含了拍摄的所有素材，通常是内部使用的，方便后期修改。
- **工作版**：接近最终版的工作版本，主要用于内部审查或测试放映。工作版可能还未进行最终的音效、配乐和视觉特效处理。
- **粉丝剪辑版**：由影迷基于原片素材重新剪辑的版本，可能会有不同的故事线，可能会删减片段或增加内容，以满足特定粉丝群体的喜好。

### 发行版本
发行版本模块目前支持 14 种发行版本，该模块会优先使用电影的文件名匹配发行版本信息，若存在多个视频文件，则会使用文件大小最大的视频文件进行匹配，若找不到发行版本信息，则会通过文件内嵌的视频标题进行匹配，若匹配到多个发行版本，则会依次写入发行版本信息，若依然找不到发行版本信息，则不会写入发行版本信息。支持的发行版本如下：

- **特别版**：包含了院线版没有的额外内容，如幕后花絮、删减场景、制作特辑等。特别版通常为影迷提供了更多的观看内容。
- **数字修复版**：对老旧影片进行数字修复的版本。此版本通常用于经典影片的再发行，确保影片的视觉和听觉效果达到现代标准。
- **3D 版**：通过 3D 技术处理后的版本，提供立体视觉效果。观众需要佩戴 3D 眼镜观看，以获得沉浸式体验。
- **IMAX 版**：为 IMAX 影院格式优化的版本，具有更好的画质和音效，提供更大、更清晰的屏幕显示和更震撼的观影体验。
- **收藏版**：通常包含豪华包装和独家附加内容，如艺术画册、模型或其他收藏品，针对电影爱好者和收藏家设计。
- **周年纪念版**：为庆祝影片上映的重要周年纪念而发行的特别版本，通常包含额外内容和纪念性附加物品。
- **终极版**：最全面和完整的版本，包含所有可能的附加内容，如导演评论、幕后花絮、删减场景等，提供最丰富的观看体验。
- **蓝光版**：以蓝光光盘格式发行的版本，拥有高画质和高音质，通常包含额外内容和特别花絮。
- **DVD 版**：以 DVD 格式发行的版本，适用于家庭播放设备。DVD 版通常也包含一些额外内容和花絮。
- **限量版**：限量发行的版本，通常具有独特的包装和附加内容，针对特定市场或收藏家设计。
- **纪念版**：为纪念某个特定事件或周年而发行的版本，包含特别设计的包装和纪念性附加内容。
- **豪华版**：包含了丰富的附加内容和豪华包装，通常提供比标准版更多的特辑和幕后花絮。
- **导演签名版**：导演亲自签名和认可的版本，通常包含导演的独家评论和特别花絮，具有较高的收藏价值。
- **标准收藏版**：由 Criterion Collection 发行的版本，专注于高品质的电影修复和特别附加内容，以电影爱好者和收藏家为目标受众。

### 片源版本
片源版本模块目前支持 25 种片源版本，该模块会优先使用电影的文件名匹配片源版本信息，若存在多个视频文件，则会使用文件大小最大的视频文件进行匹配，若找不到片源版本信息，则会通过文件内嵌的视频标题进行匹配，若依然找不到片源版本信息，则不会写入片源版本信息。支持的片源版本如下：

- **REMUX**：从蓝光光盘中提取的无损版本，没有经过压缩处理，保持了原始的画质和音质。
- **BD**：从蓝光光盘中提取的版本，经过了一些压缩处理，但画质和音质都非常好。
- **BDRIP**：从蓝光光盘压缩而来的版本，体积较小，质量比蓝光版稍差。
- **WEB-DL**：从网络流媒体服务下载的版本，画质和音质较好。
- **VODRIP**：从视频点播服务录制的版本，画质和音质较好，接近 WEB-DL。
- **WEBRIP**：从网络流媒体服务录制的版本，画质和音质不及 WEB-DL。
- **HDRIP**：从高清来源提取后压缩而来的版本，画质和音质较好。
- **HR-HDTV**：高分辨率的 HDTV 版本，经过了一些压缩处理，质量优于普通的 HDTV。
- **HDTV**：从电视广播录制的高清版本，画质较好，但可能包含电视台的水印和广告。
- **PDTV**：从数字电视录制的版本，质量比 SDTV 好，接近 HDTV。
- **DVD**：从 DVD 光盘中提取的版本，画质和音质较好。
- **DVDRIP**：从 DVD 光盘压缩而来的版本，画质和音质不及 DVD。
- **DVDSCR**：发行给奖项评审或影评人的版本，画质和音质相对较好，但可能包含水印和版权信息。
- **R5**：俄罗斯发行的 DVD 版本，画质较好，但音质可能略差。
- **LDRIP**：从激光光盘中提取的版本，画质和音质较好，但略低于 DVD。
- **PPVRIP**：从付费点播服务录制的版本，质量一般不错。
- **SDTV**：从标清电视录制的版本，分辨率较低，质量适中。
- **TVRIP**：从电视广播录制的版本，质量一般，可能包含电视台的水印和广告。
- **VHSRIP**：从 VHS 录影带中提取的版本，画质和音质略差。
- **HDTC**：从电影院胶片转录而来的高清版本，可能包含电影院现场的背景噪音。
- **TC**：从电影院胶片转录而来的标清版本，画质和音质相对较差。
- **HDCAM**：使用高清摄像设备在电影院内录制的版本，质量介于 HDTC 和普通 CAM 之间。
- **HQCAM**：使用高清摄像设备在电影院内录制的版本，画质和音质较差。
- **TS**：使用专业摄像设备在电影院内录制的版本，音质相对较好，但画质较差。
- **CAM**：使用普通摄像设备在电影院内录制的版本，画质和音质很差。

### 分辨率
分辨率模块支持 Plex 可识别的所有分辨率，该模块会从电影元数据的媒体信息中获取视频文件的分辨率信息，若存在多个视频文件，则会获取文件大小最大的视频文件的分辨率信息，若找不到分辨率信息，则不会写入分辨率信息。支持的分辨率包括但不限于：

- **8K**：包括 7680 x 4320（8K UHD）和 8192 x 4320（8K DCI）等。
- **4K**：包括 3840 x 2160（4K UHD）、3996 x 2160、4096 x 1716 和 4096 x 2160（4K DCI）等。
- **2.7K**：包括 2704 x 1520 和 3440 x 1440 等。
- **2K**：包括 1998 x 1080、2048 x 858 和 2048 x 1080（2K DCI）等。
- **1080P**：包括 1920 x 800、1920 x 818、1920 x 1034 和 1920 x 1080（FHD）等。
- **720P**：包括 1280 x 540、1280 x 640、1280 x 692 和 1280 x 720（HD）等。
- **576P**：包括 720 x 576（PAL）、768 x 576、960 x 576 和 1024 x 576 等。
- **480P**：包括 640 x 480（NTSC）、848 x 480 和 854 x 480 等。
- **SD**：包括 480P 以下的分辨率，如 360 x 240、426 x 240、480 x 360 和 640 x 360 等。

### 动态范围
动态范围模块支持 Plex 可识别的所有动态范围，该模块会从电影元数据的媒体信息中获取视频文件的动态范围信息，若存在多个视频文件，则会获取文件大小最大的视频文件的动态范围信息，若找不到动态范围信息，则不会写入动态范围信息。支持的动态范围包括但不限于：

- **DV P8**：杜比视界 P8 为流媒体提供高效色彩编码，与 HDR10 兼容，确保广泛设备支持，但色彩表现不及 P5。
- **DV P7**：杜比视界 P7 是专为蓝光原盘设计的双层格式，提供卓越的色彩深度和细节，但需要播放硬件支持。
- **DV P5**：杜比视界 P5 是针对流媒体的单层格式，色彩编码优于 P8，最适合展示杜比视界原生内容的细腻色彩。
- **HDR**：高动态范围扩展了显示设备的亮度和颜色范围，使图像更加丰富和真实，提升了观影的沉浸感。
- **SDR**：标准动态范围是传统视频格式，虽然亮度和颜色范围有限，但因其高兼容性而广泛应用于各种设备。

注：HDR10、HDR10+、HLG 等高动态范围技术都将被视作 HDR。若视频文件同时支持 HDR 和 DV，那么它们都会被写入版本信息。

### 视频编码
视频编码模块支持 Plex 可识别的所有视频编码，该模块会从电影元数据的媒体信息中获取视频文件的视频编码信息，若存在多个视频文件，则会获取文件大小最大的视频文件的视频编码信息，若找不到视频编码信息，则不会写入视频编码信息。支持的视频编码包括但不限于：

- **AV1**：全称 AOMedia Video 1，由开放媒体联盟开发的开源编码格式，具有极高的压缩效率和优秀的视频质量。
- **HEVC**：也叫 H.265，高效视频编码，提供较高的压缩效率和良好的视频质量。
- **VP9**：由 Google 开发的开源编码格式，压缩效率高，多用于 YouTube 等网络视频平台。
- **H264**：也叫 H.264 或 AVC，常见的高清视频编码格式，压缩效率较高，广泛应用于流媒体和视频存储。
- **VC1**：也叫 SMPTE 421M，微软开发的视频编码格式，压缩效率较好，多用于蓝光光盘和网络视频。
- **MPEG4**：全称 MPEG-4 Part 2，广泛应用于视频流和光盘的视频编码格式，压缩效率较好。
- **SVQ3**：全称 Sorenson Video 3，早期的视频压缩格式，压缩效率较低。
- **WMV3**：也叫 Windows Media Video 9，微软的视频编码格式，压缩效率一般。
- **WMV2**：也叫 Windows Media Video 8，较早期的微软视频编码格式，压缩效率较低。
- **WMV1**：也叫 Windows Media Video 7，最早期的微软视频编码格式，压缩效率较低。
- **MPEG2**：也叫 H.262，标准的 DVD 和部分电视广播的视频编码格式，压缩效率较低。
- **MPEG1**：早期的视频压缩格式，多用于 VCD，压缩效率很低。
- **RV40**：全称 RealVideo 4.0，RealNetworks 开发的编码格式，压缩效率较低。

### 帧率
帧率模块支持 Plex 可识别的所有帧率，该模块会从电影元数据的媒体信息中获取视频文件的帧率信息，若存在多个视频文件，则会获取文件大小最大的视频文件的帧率信息，若找不到帧率信息，则不会写入帧率信息。支持的帧率包括但不限于：

- **240P**：每秒显示 240 帧画面，用于超级慢动作视频拍摄，捕捉快速运动的细节。
- **120P**：每秒显示 120 帧画面，用于高帧率视频拍摄和播放，常见于高端电视和虚拟现实内容，提供极为流畅的视觉体验。
- **100P**：每秒显示 100 帧画面，主要用于某些高帧率的电视广播。
- **72P**：每秒显示 72 帧画面，虽不常见，但可用于某些特殊的电影放映。
- **60P**：每秒显示 60 帧画面，常用于高速运动视频、体育赛事和视频游戏，提供极其流畅的运动表现。
- **50P**：每秒显示 50 帧画面，多用于欧洲的高清电视标准以及一些高帧率的视频内容。
- **48P**：每秒显示 48 帧画面，曾用于部分电影，如《霍比特人》系列，提供比 24 帧更流畅的画面。
- **30P**：每秒显示 30 帧画面，适用于 NTSC 制式的视频标准，广泛应用于北美和日本的电视广播。
- **25P**：每秒显示 25 帧画面，适用于 PAL 制式的视频标准，主要用于欧洲、中国、澳大利亚和其他采用 PAL 制式的地区的电视和视频内容。
- **24P**：每秒显示 24 帧画面，传统的电影帧率，常用于电影制作，带来独特的电影质感。
- **15P**：每秒显示 15 帧画面，多用于低带宽的视频流和某些网络摄像头。
- **12P**：每秒显示 12 帧画面，曾用于早期的动画和低带宽的视频传输。
- **10P**：每秒显示 10 帧画面，主要用于非常低带宽的视频传输和某些监控摄像头。
- **5P**：每秒显示 5 帧画面，用于极低带宽的监控和视频传输。

### 音频编码
音频编码模块支持 Plex 可识别的所有音频编码，该模块会从电影元数据的媒体信息中获取视频文件的音频编码信息，若存在多个视频文件，则会获取文件大小最大的视频文件的音频编码信息，若存在多个音频流，则会获取比特率最高的音频流的音频编码信息（多声道优先），若找不到音频编码信息，则不会写入音频编码信息。支持的音频编码包括但不限于：

- **DTS-HD MA**：全称 DTS-HD Master Audio，是无损编码，提供电影院级的音质，常用于蓝光光盘。
- **TRUEHD**：全称 Dolby TrueHD，是杜比无损编码，提供高保真音质，也常用于蓝光光盘。
- **FLAC**：全称 Free Lossless Audio Codec，是开源无损编码，广泛用于音乐存档和高保真音轨。
- **PCM**：全称 Pulse Code Modulation，是无损编码，提供原始音质，常用于 CD 和 DVD。
- **DTS-HD HRA**：全称 DTS-HD High Resolution Audio，是高分辨率音频，有损编码，音质优于标准 DTS。
- **DTS-ES**：全称 DTS Extended Surround，是扩展环绕声，为 DTS 的扩展版本，增加了一个后置中央声道。
- **EAC3**：全称 Enhanced AC-3，也叫 Dolby Digital Plus，杜比数字的加强版，提供更高的压缩比和更好的音质。
- **DTS**：全称 Digital Theater Systems，数字影院系统编码，广泛用于电影和 DVD。
- **AC3**：也叫 Dolby Digital，杜比数字编码，常用于 DVD 和数字电视广播。
- **HE-AAC**：全称 High-Efficiency Advanced Audio Codec，高效率高级音频编码，相比 AAC 提供了更高的数据压缩率。
- **AAC**：全称 Advanced Audio Codec，高级音频编码，是 MP3 的继任者，广泛用于流媒体。
- **MP3**：全称 MPEG-1 Audio Layer 3，是最常见的有损音频编码，广泛用于音乐播放。
- **VORBIS**：全称 Ogg Vorbis，是开源有损编码，常用于游戏和网络音频。
- **WMAPRO**：全称 Windows Media Audio Professional，是微软开发的有损编码，提供较高音质。
- **COOK**：全称 RealAudio COOK，是 RealNetworks 开发的有损编码，主要用于早期的流媒体。
- **MP2**：全称 MPEG-1 Audio Layer 2，是早期的有损编码，常用于广播和 VCD。
- **WMAV2**：全称 Windows Media Audio Version 2，是 WMA 的一个变体，提供较高的音频压缩率和较低的音质。
- **WMA**：全称 Windows Media Audio，是微软开发的有损编码，广泛用于 Windows 平台。

注：在写入版本信息时，音频编码后方会显示对应音频流的声道信息，如 TRUEHD 7.1、AC3 5.1、AAC 立体声等等。

### 比特率
比特率模块会从电影元数据的媒体信息中获取视频文件的比特率（码率）信息，若存在多个视频文件，则会获取文件大小最大的视频文件的比特率信息，若找不到比特率信息，则不会写入比特率信息（比特率的单位为 Kbps、Mbps）。

### 大小
大小模块会从电影元数据的媒体信息中获取视频文件的（文件）大小信息，若存在多个视频文件，则会获取文件大小最大的视频文件的大小信息（大小的单位为 B、KB、MB、GB）。

### 国家
国家模块会从电影元数据中获取电影的（制片）国家（或地区）信息，若存在多个国家，则会依次写入国家信息，若找不到国家信息，则不会写入国家信息。

### 内容分级
内容分级模块会从电影元数据中获取电影的内容分级信息，若找不到内容分级信息，则不会写入内容分级信息。支持的内容分级包括但不限于：

#### 电影分级（MPAA）
- **G**：全称 General Audiences，适合所有年龄段观众，不包含任何不适合儿童观看的内容。
- **PG**：全称 Parental Guidance Suggested，建议家长给予指导，可能包含一些不适合儿童的内容。
- **PG-13**：也叫 Parents Strongly Cautioned，强烈建议家长给予指导，部分内容可能不适合 13 岁以下的儿童。
- **R**：全称 Restricted，17 岁以下观众需由家长或成年监护人陪同观看，包含激烈的语言、暴力或性内容。
- **NC-17**：也叫 Adults Only，仅限 17 岁及以上观众观看，包含非常明确的暴力或性内容。
- **NR**：全称 Not Rated，影片未经过 MPAA 的审查和评级。
- **Unrated**：未经官方评级机构如 MPAA 评级的版本，可能包含原始评级版本中删减的内容。

#### 电视节目分级（TV Parental Guidelines）
- **TV-Y**：全称 Television for All Children，适合所有儿童观看，通常适合 2-6 岁的儿童。
- **TV-Y7**：全称 Television for Children 7 and Above，适合 7 岁及以上儿童观看，可能包含轻微暴力或复杂的情节。
- **TV-Y7-FV**：全称 Television for Children 7 and Above - Fantasy Violence，适合 7 岁及以上儿童观看，包含幻想暴力元素。
- **TV-G**：全称 Television General Audience，适合所有年龄段观众，节目中不包含任何不适合儿童观看的内容。
- **TV-PG**：全称 Television Parental Guidance Suggested，建议家长给予指导，可能包含一些不适合儿童的内容。
- **TV-14**：全称 Television Parents Strongly Cautioned，强烈建议家长给予指导，部分内容可能不适合 14 岁以下的儿童。
- **TV-MA**：全称 Television Mature Audience Only，仅限成年观众观看，可能包含激烈的语言、暴力或性内容。

#### 其他分级标准
- **Approved**：电影获得电影协会的认可，适合公众观看，具体内容依据发行年代不同而有所变化。
- **18+**：仅限 18 岁及以上观众观看，内容非常成人化。
- **AO**：全称 Adults Only，用于视频游戏的评级，仅限成人观看。

注：上述分级为美国的分级制度说明，其它地区的分级制度可能存在差异，以实际情况为准。由于中国大陆地区没有内容分级制度，建议将 “认证国家/地区” 设置为 “美国”，以获取内容分级信息。

### 评分
评分模块会从电影元数据中获取电影的（观众）评分信息（使用资料库设置的评分来源），若找不到评分信息，则不会写入评分信息（评分将转换为十分制）。

### 时长
时长模块会从电影元数据的媒体信息中获取视频文件的时长信息，若存在多个视频文件，则会获取文件大小最大的视频文件的时长信息，若找不到时长信息，则不会写入时长信息（时长的单位为分钟）。

## 功能
EMP 共有 `为所有电影添加版本信息（all）`、`为新增电影添加版本信息（new）` 和 `为所有电影重置版本信息（reset）` 三种运行模式：

- 为所有电影添加版本信息：根据用户配置，在排除掉需要跳过的资料库后为其余库中的所有电影添加版本信息，已经存在版本信息的电影会被跳过。
- 为新增电影添加版本信息：通过 Webhooks 功能监听服务器事件，实时获取新增项目的元数据，根据用户配置，仅为新增电影（不含需要跳过的资料库中的新增电影）添加版本信息。
- 为所有电影重置版本信息：根据用户配置，在排除掉需要跳过的资料库后为其余库中的所有电影重置（移除）版本信息。

注：`为新增电影添加版本信息` 模式需要服务器的管理员账号订阅了 Plex Pass 才能使用。

## 配置说明
运行前，请先参考以下提示（示例）对 `/config/config.ini` 进行配置。
```
> 💡 On Windows, you can double-click `edition_manager_gui.pyw` to launch it directly.
[server]
# Plex 服务器的地址，格式为 http://服务器 IP 地址:32400 或 http(s)://域名:端口号
address = http://127.0.0.1:32400
# Plex 服务器的 token，用于身份验证
token = xxxxxxxxxxxxxxxxxxxx
# 指定需要跳过的资料库，格式为库名1；库名2；库名3，若没有需要跳过的资料库，可以留空
skip_libraries = 云电影；演唱会
# 语言设置，zh 代表中文，en 代表英文
language = zh

The GUI supports:
[modules]
# 指定需要写入的模块及其排序，格式为模块1；模块2；模块3，可选模块包括剪辑版本、发行版本、片源版本、分辨率、动态范围、视频编码、帧率、音频编码、比特率、大小、国家、内容分级、评分、时长
order = 片源版本；动态范围
```
由于 EMP 只会对电影和其他影片类型的资料库进行处理，所以在指定需要跳过的资料库时，指定需要跳过的电影和其他影片类型的资料库即可。写入版本信息的模块没有数量限制，可以根据需要自行选配。

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
- 如果无法连接到 Plex 服务器，请检查你的网络连接，并确保服务器可以访问。如果你是通过 Docker 容器运行的，也可以尝试使用 `host` 模式重新部署容器运行。
- 请使用服务器管理员账号的 X-Plex-Token，以确保你拥有足够的权限进行操作。
- 版本信息将在添加后被锁定，若有修改需求，Plex Pass 订阅用户可以手动解锁版本信息，然后进行修改；非 Plex Pass 订阅用户不支持手动修改版本信息。若要为所有电影修改版本信息的模块或排序，请先重置版本信息，然后修改配置文件，再重新写入版本信息。
- 修改配置文件后，需要重启容器，新的配置信息才会生效。
- 若脚本在 Windows 上运行后没有反应，请将运行命令或启动脚本中的 `python3` 替换为 `python` 再运行。
- 如需使用 `为新增电影添加版本信息` 模式，请确保你在服务器的 `设置 - 网络` 中勾选了 `Webhooks` 选项。

`max_workers` - Number of concurrent threads

`batch_size` - Movies processed per batch
<img width="399" alt="赞赏" src="https://github.com/x1ao4/edition-manager-for-plex/assets/112841659/b9e79a88-f2af-4c3a-8278-479454c6393a">
## 赞赏
如果你觉得这个项目对你有用，可以考虑请我喝杯咖啡或者给我一个⭐️。谢谢你的支持！

<img width="383" alt="赞赏" src="https://github.com/user-attachments/assets/bdd2226b-6282-439d-be92-5311b6e9d29c">
<br><br>
<a href="#edition-manager-for-plex-zh">回到顶部</a>
<br>
<br>
<br>

## Previews

Different module combinations yield unique Edition styles:
In Plex, there are two concepts of "version": "[Edition](https://support.plex.tv/articles/multiple-editions/)" and "[Version](https://support.plex.tv/articles/200381043-multi-version-movies/)", but their uses are quite different.

The primary design of Edition is to differentiate between various cut versions of a film, such as Theatrical Cut, Director's Cut, Extended Cut, Unrated Cut, etc. If you have different cut versions of the same movie, you can label and distinguish them by editing the Edition in Plex. These different versions will be displayed as separate entries in the media library, each with its own viewing status, progress, and rating records, independent of each other.

The primary design of Version is to integrate multiple file versions of the same cut, mainly referring to different resolutions, encoding formats, or dynamic ranges, such as 1080P, 4K, SDR, HDR, etc. If you have different file versions of the same movie, they will automatically merge into a single entry in the media library after successful matching. You can choose which version to watch through "Play Version" during playback (if not selected, the default version will be played). They will share the same viewing status, progress, and rating records.

The Edition is displayed below the title, after the year, and also in the "More Ways to Watch/Watch From These Locations" section, and it supports custom display names. In contrast, the Version is only shown on the movie's detail page and does not support custom display names. Since the actual use cases for marking different cut versions are not frequent and the Edition's display position is quite prominent, we can fully utilize this feature to mark other information about the movie beyond just different cuts.

For instance, currently, Plex's mobile and TV apps do not display Dolby Vision information. We can achieve this by writing the dynamic range into the Edition, allowing Dolby Vision information to be displayed on mobile and TV apps. This way, we can distinguish which movies are Dolby Vision versions. Additionally, Plex's library sorting currently only supports single sorting criteria. You cannot display the movie's resolution or bitrate information while sorting by title or audience rating. Similarly, we can display this extra information through Edition.

Using Edition Manager for Plex (hereafter referred to as EMP), you can automatically retrieve information about movies and movie files and write the specified information into the Edition field, enriching the display functionality of movie information. With EMP, you can write the movie's Cut Version, Release Version, Source Version, Resolution, Dynamic Range, Video Codec, Frame Rate, Audio Codec, Bitrate, Size, Country, Content Rating, Audience Rating, or Duration into the Edition field. It also supports custom modules and custom sorting. 

All of this will be automatically handled by EMP, without the need to edit or modify filenames. This means you don't need to add Edition information to the filename in the format `{edition-Edition Title}`. EMP will automatically search for relevant information through filenames or the movie's metadata, and then write the required details into the Edition field. There are no specific requirements for naming files.

You can use EMP to add extra display information to your movies according to your needs and preferences. We provide features for writing and removing Editions, allowing you to try any combination freely and remove all Edition information with one click at any time. Although Edition is an exclusive feature for Plex Pass, EMP allows you to use the Edition feature without a Pass subscription.

## Examples
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

## Configuration
Before running, please configure the `/config/config.ini` file according to the following tips (example).
```
[server]
# Address of the Plex server, formatted as http://server IP address:32400 or http(s)://domain:port
address = http://127.0.0.1:32400
# Token of the Plex server for authentication
token = xxxxxxxxxxxxxxxxxxxx
# Specify libraries to skip, format should be LibraryName1;LibraryName2;LibraryName3, leave empty if no libraries need to be skipped
skip_libraries = Cloud Movie;Concert
# Language setting, zh for Chinese, en for English
language = en

[modules]
# Specify modules to write and their order, format should be Module1;Module2;Module3, optional modules include Cut, Release, Source, Resolution, DynamicRange, VideoCodec, FrameRate, AudioCodec, Bitrate, Size, Country, ContentRating, Rating, Duration
order = Source;DynamicRange
```
Since EMP only processes movie-type libraries, specify Movies and Other Videos libraries to skip when needed. There is no limit to the number of modules for writing editions, so you can choose and configure them according to your needs.

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

#### How to Use
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
- All required dependencies installed using `pip3 install -r requirements.txt`.

#### How to Use
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

#### Auto-Run Setup
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
- If the script or container cannot connect to the Plex server, please check your network connection and ensure the server is accessible. If you are running it through a Docker container, you can also try redeploying the container using the `host` mode.
- Please use the X-Plex-Token of the server administrator account to ensure you have sufficient permissions to perform operations.
- The edition field will be locked after being added. If modifications are needed, Plex Pass subscribers can manually unlock the edition field and then modify it; non-Plex Pass subscribers do not support manual modification of the edition field. To modify the edition modules or their order for all movies, first reset the editions, then modify the configuration file, and finally rewrite the editions.
- After modifying the configuration file, you need to restart the container for the new configuration to take effect.
- If it doesn't respond on Windows, try replacing `python3` with `python` in the run command or start script.
- To use the `add editions for new movies` mode, please ensure you have checked the `Webhooks` option in the server's `Settings - Network` section.

## Support

If you enjoy Edition Manager, please consider giving it a **⭐ on GitHub**  
or [buying me a slice of pizza 🍕](https://www.buymeacoffee.com/Entree).  

Your support helps keep development going!
<img width="399" alt="Support" src="https://github.com/x1ao4/edition-manager-for-plex/assets/112841659/b9e79a88-f2af-4c3a-8278-479454c6393a">
<img width="383" alt="Support" src="https://github.com/user-attachments/assets/bdd2226b-6282-439d-be92-5311b6e9d29c">
<br><br>
<a href="#edition-manager-for-plex-en">Back to Top</a>
