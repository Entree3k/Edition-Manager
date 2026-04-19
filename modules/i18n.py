"""Minimal i18n helper. Supports English and Chinese.

Usage:
    from modules.i18n import set_locale, t
    set_locale('auto')   # or 'en' / 'zh'
    logger.info(t('connected', name=server_name))
"""
import locale as _locale

TRANSLATIONS = {
    # Connection / lifecycle
    'connected': {
        'en': 'Successfully connected to server: {name}',
        'zh': '已成功连接到服务器：{name}',
    },
    'connect_failed': {
        'en': 'Server connection failed, please check the settings in the configuration file or your network.',
        'zh': '服务器连接失败，请检查配置文件或网络的设置是否有误。',
    },
    'script_done': {
        'en': 'Script execution completed.',
        'zh': '脚本执行完毕。',
    },

    # Library enumeration
    'total_movies': {
        'en': 'Total movies found: {count}',
        'zh': '共找到 {count} 部电影',
    },
    'library_count': {
        'en': 'Library: {title}, Movies: {count}',
        'zh': '资料库：{title}，电影数：{count}',
    },

    # Batch processing
    'batch_prefetching': {
        'en': 'Batch {num}/{total}: Prefetching metadata for {count} movies...',
        'zh': '批次 {num}/{total}：正在预取 {count} 部电影的元数据...',
    },
    'batch_prefetched': {
        'en': 'Batch {num}/{total}: Prefetched {count} metadata entries',
        'zh': '批次 {num}/{total}：已预取 {count} 条元数据',
    },

    # Per-movie actions
    'cleared_edition': {
        'en': '{title}: Cleared edition information',
        'zh': '{title}：已清除 Edition 信息',
    },
    'processing_key': {
        'en': 'Processing ratingKey={key} ...',
        'zh': '正在处理 ratingKey={key} ...',
    },
    'movie_not_found': {
        'en': 'Movie with ratingKey {key} not found.',
        'zh': '未找到 ratingKey 为 {key} 的电影。',
    },
    'done': {
        'en': 'Done.',
        'zh': '完成。',
    },
    'failed': {
        'en': 'Failed.',
        'zh': '失败。',
    },

    # Interactive --one flow
    'no_title_entered': {
        'en': 'No title entered.',
        'zh': '未输入标题。',
    },
    'no_movies_found': {
        'en': "No movies found for '{title}'.",
        'zh': "未找到与 '{title}' 匹配的电影。",
    },
    'prompt_enter_title': {
        'en': 'Enter movie title to search: ',
        'zh': '请输入要搜索的电影标题：',
    },
    'prompt_select_number': {
        'en': '\nSelect a number (or Enter for 1): ',
        'zh': '\n请选择编号（按回车默认选 1）：',
    },
    'found_matches': {
        'en': '\nFound {count} match(es):',
        'zh': '\n找到 {count} 个匹配结果：',
    },
    'invalid_selection': {
        'en': 'Invalid selection.',
        'zh': '选择无效。',
    },
    'prompt_confirm': {
        'en': "Process '{title}' ({year}) from {library}? [y/N]: ",
        'zh': "是否处理 '{title}' ({year}) 来自 {library}？[y/N]：",
    },
    'cancelled': {
        'en': 'Cancelled.',
        'zh': '已取消。',
    },

    # Reset
    'total_reset': {
        'en': 'Total movies to reset: {count}',
        'zh': '待重置的电影数量：{count}',
    },
    'reset_one': {
        'en': 'Reset: {title}',
        'zh': '已重置：{title}',
    },
    'reset_batch': {
        'en': 'Reset batch {num}/{total}',
        'zh': '已重置批次 {num}/{total}',
    },
    'reset_error': {
        'en': 'Error resetting movie {title}: {err}',
        'zh': '重置电影 {title} 出错：{err}',
    },

    # Backup / Restore / Undo
    'backup_completed': {
        'en': 'Metadata backup completed.',
        'zh': '元数据备份完成。',
    },
    'restore_completed': {
        'en': 'Metadata restoration completed.',
        'zh': '元数据恢复完成。',
    },
    'no_backups_found': {
        'en': 'No backups found in {path}',
        'zh': '在 {path} 中未找到备份。',
    },
    'available_backups': {
        'en': 'Available backups:',
        'zh': '可用的备份：',
    },
    'listed_backups': {
        'en': 'Listed backups.',
        'zh': '已列出备份。',
    },
    'no_backup_files': {
        'en': 'No backup files found.',
        'zh': '未找到备份文件。',
    },
    'using_latest_backup': {
        'en': 'Using latest backup: {path}',
        'zh': '正在使用最新备份：{path}',
    },
    'backup_not_found': {
        'en': 'Backup file not found: {path}',
        'zh': '未找到备份文件：{path}',
    },
    'starting_restore': {
        'en': 'Starting restore from {path} for {count} movies',
        'zh': '开始从 {path} 为 {count} 部电影恢复',
    },
    'restore_failed': {
        'en': 'Failed restore id={id}: {err}',
        'zh': '恢复失败 id={id}：{err}',
    },
    'restore_complete': {
        'en': 'Restore complete.',
        'zh': '恢复完成。',
    },
    'undo_snapshot_created': {
        'en': 'Undo snapshot created with {count} movies.',
        'zh': '已创建包含 {count} 部电影的撤销快照。',
    },
    'undo_snapshot_creating_process': {
        'en': 'Creating undo snapshot before processing...',
        'zh': '正在处理前创建撤销快照...',
    },
    'undo_snapshot_creating_reset': {
        'en': 'Creating undo snapshot before reset...',
        'zh': '正在重置前创建撤销快照...',
    },
    'undo_no_snapshot': {
        'en': 'No undo snapshot available.',
        'zh': '没有可用的撤销快照。',
    },
    'undo_empty': {
        'en': 'Undo snapshot is empty.',
        'zh': '撤销快照为空。',
    },
    'undo_restoring': {
        'en': 'Restoring from undo snapshot ({count} movies)...',
        'zh': '正在从撤销快照恢复（{count} 部电影）...',
    },
    'undo_restore_complete': {
        'en': 'Undo restore complete.',
        'zh': '撤销恢复完成。',
    },
    'undo_success': {
        'en': 'Undo completed successfully.',
        'zh': '撤销操作成功完成。',
    },
    'undo_failed': {
        'en': 'Undo failed - no snapshot available or restore error.',
        'zh': '撤销失败 — 无可用快照或恢复出错。',
    },

    # Help / usage
    'no_action': {
        'en': 'No action specified. Please use one of the following arguments:',
        'zh': '未指定操作。请使用以下参数之一：',
    },
    'help_all': {
        'en': '  --all: Add edition info to all movies',
        'zh': '  --all：为所有电影添加 Edition 信息',
    },
    'help_one': {
        'en': '  --one: Add edition info to one movie',
        'zh': '  --one：为单部电影添加 Edition 信息',
    },
    'help_reset': {
        'en': '  --reset: Reset edition info for all movies',
        'zh': '  --reset：重置所有电影的 Edition 信息',
    },
    'help_backup': {
        'en': '  --backup: Backup movie metadata',
        'zh': '  --backup：备份电影元数据',
    },
    'help_restore': {
        'en': '  --restore: Restore movie metadata from backup',
        'zh': '  --restore：从备份恢复电影元数据',
    },

    # Generic errors
    'unknown_module': {
        'en': 'Unknown module: {name}',
        'zh': '未知模块：{name}',
    },
    'processing_error': {
        'en': 'Error processing movie {title}: {err}',
        'zh': '处理电影 {title} 出错：{err}',
    },
}

_current = 'en'


def _detect_system_locale():
    try:
        code = _locale.getlocale()[0] or _locale.getdefaultlocale()[0] or ''
    except Exception:
        code = ''
    return 'zh' if code.lower().startswith('zh') else 'en'


def set_locale(code):
    """Set active locale. Accepts 'en', 'zh', or 'auto'."""
    global _current
    code = (code or 'auto').strip().lower()
    if code in ('auto', ''):
        _current = _detect_system_locale()
    elif code.startswith('zh'):
        _current = 'zh'
    else:
        _current = 'en'
    return _current


def get_locale():
    return _current


def t(key, **kwargs):
    """Return translated message. Falls back to English, then to the key itself."""
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key.format(**kwargs) if kwargs else key
    msg = entry.get(_current) or entry.get('en') or key
    return msg.format(**kwargs) if kwargs else msg
