use std::{
    fs::{self, OpenOptions},
    net::TcpListener,
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::Mutex,
};

use serde::Serialize;
use tauri::{
    AppHandle, LogicalSize, Manager, PhysicalPosition, Position, RunEvent, State, WindowEvent,
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
};
use uuid::Uuid;

const PREFERRED_AGENT_PORT: u16 = 8765;
const DONATION_URL: &str = "https://buymeacoffee.com/jeromerlon";

struct AgentState {
    token: String,
    port: u16,
    launch_error: Option<String>,
    child: Mutex<Option<Child>>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct AgentConnection {
    base_url: String,
    token: String,
    launch_error: Option<String>,
}

#[tauri::command]
fn agent_connection(state: State<'_, AgentState>) -> AgentConnection {
    AgentConnection {
        base_url: format!("http://127.0.0.1:{}", state.port),
        token: state.token.clone(),
        launch_error: state.launch_error.clone(),
    }
}

#[tauri::command]
fn open_donation_page() -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x08000000;
        Command::new("rundll32.exe")
            .args(["url.dll,FileProtocolHandler", DONATION_URL])
            .creation_flags(CREATE_NO_WINDOW)
            .spawn()
            .map(|_| ())
            .map_err(|error| format!("Unable to open the donation page: {error}"))
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(DONATION_URL)
            .spawn()
            .map(|_| ())
            .map_err(|error| format!("Unable to open the donation page: {error}"))
    }

    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(DONATION_URL)
            .spawn()
            .map(|_| ())
            .map_err(|error| format!("Unable to open the donation page: {error}"))
    }

    #[cfg(not(any(target_os = "windows", target_os = "macos", target_os = "linux")))]
    Err("Opening the donation page is not supported on this platform".to_owned())
}

#[tauri::command]
fn show_main_window(app: AppHandle) -> Result<(), String> {
    let window = app
        .get_webview_window("main")
        .ok_or_else(|| "Main window not found".to_owned())?;
    window.show().map_err(|error| error.to_string())?;
    window.unminimize().map_err(|error| error.to_string())?;
    window.set_focus().map_err(|error| error.to_string())
}

#[tauri::command]
fn finish_splash(app: AppHandle) -> Result<(), String> {
    if let Some(splash) = app.get_webview_window("splash") {
        splash.hide().map_err(|error| error.to_string())?;
    }

    let main = app
        .get_webview_window("main")
        .ok_or_else(|| "Main window not found".to_owned())?;
    let status = app
        .get_webview_window("status")
        .ok_or_else(|| "Status window not found".to_owned())?;

    status
        .set_size(LogicalSize::new(92.0, 114.0))
        .map_err(|error| error.to_string())?;
    position_status_window(&status);
    main.show().map_err(|error| error.to_string())?;
    main.unminimize().map_err(|error| error.to_string())?;
    status.show().map_err(|error| error.to_string())?;
    main.set_focus().map_err(|error| error.to_string())
}

#[tauri::command]
fn toggle_status_window(app: AppHandle) -> Result<(), String> {
    let window = app
        .get_webview_window("status")
        .ok_or_else(|| "Status window not found".to_owned())?;
    let visible = window.is_visible().map_err(|error| error.to_string())?;
    if visible {
        window.hide().map_err(|error| error.to_string())
    } else {
        position_status_window(&window);
        window.show().map_err(|error| error.to_string())
    }
}

#[tauri::command]
fn set_status_window_expanded(app: AppHandle, expanded: bool) -> Result<(), String> {
    let window = app
        .get_webview_window("status")
        .ok_or_else(|| "Status window not found".to_owned())?;
    let old_position = window.outer_position().map_err(|error| error.to_string())?;
    let old_size = window.outer_size().map_err(|error| error.to_string())?;
    let (width, height) = if expanded {
        (350.0, 220.0)
    } else {
        (92.0, 114.0)
    };
    window
        .set_size(LogicalSize::new(width, height))
        .map_err(|error| error.to_string())?;
    let new_size = window.outer_size().map_err(|error| error.to_string())?;
    let anchored_x = old_position.x + old_size.width as i32 - new_size.width as i32;
    let anchored_y = old_position.y + old_size.height as i32 - new_size.height as i32;
    window
        .set_position(PhysicalPosition::new(anchored_x, anchored_y))
        .map_err(|error| error.to_string())?;
    Ok(())
}

fn is_project_root(path: &Path) -> bool {
    path.join("VERSION").is_file() && path.join("apps").is_dir() && path.join("services").is_dir()
}

fn find_project_root() -> Option<PathBuf> {
    let mut starts = Vec::new();
    if let Ok(current_dir) = std::env::current_dir() {
        starts.push(current_dir);
    }
    if let Ok(executable) = std::env::current_exe()
        && let Some(parent) = executable.parent()
    {
        starts.push(parent.to_path_buf());
    }
    starts.into_iter().find_map(|start| {
        start
            .ancestors()
            .find(|candidate| is_project_root(candidate))
            .map(Path::to_path_buf)
    })
}

fn executable_dir() -> PathBuf {
    std::env::current_exe()
        .ok()
        .and_then(|path| path.parent().map(Path::to_path_buf))
        .or_else(|| std::env::current_dir().ok())
        .unwrap_or_else(|| PathBuf::from("."))
}

fn project_root() -> PathBuf {
    find_project_root().unwrap_or_else(executable_dir)
}

fn runtime_data_dir() -> PathBuf {
    std::env::var_os("STUDY_ASSISTANT_DATA_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            find_project_root()
                .unwrap_or_else(executable_dir)
                .join("runtime-data")
        })
}

fn python_executable() -> String {
    std::env::var("STUDY_ASSISTANT_PYTHON").unwrap_or_else(|_| "python".to_owned())
}

fn choose_agent_port() -> Result<u16, String> {
    if let Ok(listener) = TcpListener::bind(("127.0.0.1", PREFERRED_AGENT_PORT)) {
        drop(listener);
        return Ok(PREFERRED_AGENT_PORT);
    }
    let listener = TcpListener::bind(("127.0.0.1", 0))
        .map_err(|error| format!("Unable to reserve a local Agent port: {error}"))?;
    let port = listener
        .local_addr()
        .map_err(|error| format!("Unable to read the local Agent port: {error}"))?
        .port();
    drop(listener);
    Ok(port)
}

fn packaged_agent_executable() -> Option<PathBuf> {
    let file_name = if cfg!(windows) {
        "study-assistant-agent.exe"
    } else {
        "study-assistant-agent"
    };
    let executable = std::env::current_exe().ok()?;
    let executable_dir = executable.parent()?;
    [
        executable_dir.join(file_name),
        executable_dir.join("resources").join(file_name),
        executable_dir.join("binaries").join(file_name),
    ]
    .into_iter()
    .find(|candidate| candidate.is_file())
}

fn configure_agent_log(command: &mut Command, data_dir: &Path) {
    if cfg!(debug_assertions) {
        command.stdout(Stdio::inherit()).stderr(Stdio::inherit());
        return;
    }
    if fs::create_dir_all(data_dir).is_err() {
        command.stdout(Stdio::null()).stderr(Stdio::null());
        return;
    }
    let Ok(log) = OpenOptions::new()
        .create(true)
        .append(true)
        .open(data_dir.join("agent.log"))
    else {
        command.stdout(Stdio::null()).stderr(Stdio::null());
        return;
    };
    match log.try_clone() {
        Ok(stdout) => {
            command.stdout(Stdio::from(stdout)).stderr(Stdio::from(log));
        }
        Err(_) => {
            command.stdout(Stdio::null()).stderr(Stdio::from(log));
        }
    }
}

fn spawn_agent(token: &str, port: u16) -> Result<Child, String> {
    let root = project_root();
    let data_dir = runtime_data_dir();
    let mut command = if !cfg!(debug_assertions) {
        packaged_agent_executable().map(Command::new)
    } else {
        None
    };
    if command.is_none() {
        let source_path = root.join("services").join("agent").join("src");
        let existing_python_path = std::env::var_os("PYTHONPATH").unwrap_or_default();
        let separator = if cfg!(windows) { ";" } else { ":" };
        let python_path = if existing_python_path.is_empty() {
            source_path.to_string_lossy().into_owned()
        } else {
            format!(
                "{}{}{}",
                source_path.to_string_lossy(),
                separator,
                existing_python_path.to_string_lossy()
            )
        };
        let mut python = Command::new(python_executable());
        python
            .arg("-m")
            .arg("study_assistant_agent")
            .current_dir(&root)
            .env("PYTHONPATH", python_path);
        command = Some(python);
    }
    let mut command = command.expect("Agent command must be configured");
    command
        .env("STUDY_ASSISTANT_HOST", "127.0.0.1")
        .env("STUDY_ASSISTANT_PORT", port.to_string())
        .env("STUDY_ASSISTANT_SESSION_TOKEN", token)
        .env("STUDY_ASSISTANT_DATA_DIR", &data_dir)
        .stdin(Stdio::null());
    configure_agent_log(&mut command, &data_dir);
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x08000000;
        command.creation_flags(CREATE_NO_WINDOW);
    }
    command
        .spawn()
        .map_err(|error| format!("Unable to launch the local Agent: {error}"))
}

fn stop_agent(app: &AppHandle) {
    if let Some(state) = app.try_state::<AgentState>() {
        if let Ok(mut guard) = state.child.lock() {
            if let Some(child) = guard.as_mut() {
                let _ = child.kill();
                let _ = child.wait();
            }
            *guard = None;
        }
    }
}

fn position_status_window(window: &tauri::WebviewWindow) {
    if let Ok(Some(monitor)) = window.primary_monitor() {
        let monitor_position = monitor.position();
        let monitor_size = monitor.size();
        if let Ok(window_size) = window.outer_size() {
            let x = monitor_position.x + monitor_size.width as i32 - window_size.width as i32 - 24;
            let y =
                monitor_position.y + monitor_size.height as i32 - window_size.height as i32 - 52;
            let _ = window.set_position(Position::Physical(PhysicalPosition::new(x, y)));
        }
    }
}

fn build_tray(app: &AppHandle) -> tauri::Result<()> {
    let show = MenuItem::with_id(app, "show", "打开主界面", true, None::<&str>)?;
    let status = MenuItem::with_id(app, "status", "显示/隐藏状态浮窗", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "quit", "退出 Study Assistant", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&show, &status, &quit])?;
    let mut builder = TrayIconBuilder::with_id("study-assistant-tray")
        .tooltip("Study Assistant")
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(|app, event| match event.id.as_ref() {
            "show" => {
                let _ = show_main_window(app.clone());
            }
            "status" => {
                let _ = toggle_status_window(app.clone());
            }
            "quit" => {
                stop_agent(app);
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                let _ = show_main_window(tray.app_handle().clone());
            }
        });
    if let Some(icon) = app.default_window_icon() {
        builder = builder.icon(icon.clone());
    }
    builder.build(app)?;
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let token = Uuid::new_v4().to_string();
    let port = choose_agent_port().unwrap_or(PREFERRED_AGENT_PORT);
    let (child, launch_error) = match spawn_agent(&token, port) {
        Ok(child) => (Some(child), None),
        Err(error) => (None, Some(error)),
    };
    tauri::Builder::default()
        .manage(AgentState {
            token,
            port,
            launch_error,
            child: Mutex::new(child),
        })
        .invoke_handler(tauri::generate_handler![
            agent_connection,
            open_donation_page,
            finish_splash,
            show_main_window,
            toggle_status_window,
            set_status_window_expanded
        ])
        .setup(|app| {
            build_tray(app.handle())?;
            if let Some(window) = app.get_webview_window("status") {
                position_status_window(&window);
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                if window.label() == "main" || window.label() == "status" {
                    api.prevent_close();
                    let _ = window.hide();
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building Study Assistant")
        .run(|app, event| {
            if matches!(event, RunEvent::Exit | RunEvent::ExitRequested { .. }) {
                stop_agent(app);
            }
        });
}
