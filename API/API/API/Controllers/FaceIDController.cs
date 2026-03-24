using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;
using System.Net.Http;
using System.Threading.Tasks;
using API.Services;
using System.Text;

namespace API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class FaceIDController : ControllerBase
    {
        private static readonly HttpClient client = new HttpClient();

        private static Process? pythonProcess;
        private static readonly StringBuilder pythonLogBuffer = new StringBuilder();
        private readonly ILanCameraDiscoveryService _lanCameraDiscoveryService;

        private const string PythonApi = "http://127.0.0.1:8000";
        private readonly string _pythonFolder = ResolvePythonFolder();

        public FaceIDController(ILanCameraDiscoveryService lanCameraDiscoveryService)
        {
            _lanCameraDiscoveryService = lanCameraDiscoveryService;
        }

        // =========================

        async Task EnsurePythonRunning()
        {
            try
            {
                var res = await client.GetAsync($"{PythonApi}/");
                if (res.IsSuccessStatusCode)
                    return;
            }
            catch { }

            StartPythonServer();

            for (int attempt = 0; attempt < 10; attempt++)
            {
                if (pythonProcess != null && pythonProcess.HasExited)
                {
                    var log = pythonLogBuffer.ToString().Trim();
                    throw new InvalidOperationException(
                        string.IsNullOrWhiteSpace(log)
                            ? "Python FaceID server da thoat truoc khi khoi dong xong."
                            : $"Python FaceID server khoi dong that bai: {log}"
                    );
                }

                try
                {
                    var res = await client.GetAsync($"{PythonApi}/");
                    if (res.IsSuccessStatusCode)
                        return;
                }
                catch { }

                await Task.Delay(1000);
            }

            throw new InvalidOperationException("Khong the ket noi toi Python FaceID server tai 127.0.0.1:8000.");
        }

        // =========================

        private static string ResolvePythonFolder()
        {
            var candidateFolders = new[]
            {
                Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "AI_Project", "face_recognition")),
                Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "..", "..", "..", "AI_Project", "face_recognition")),
                Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "AI_Project", "face_recognition"))
            };

            return candidateFolders.FirstOrDefault(Directory.Exists) ?? candidateFolders[0];
        }

        private static string ResolvePythonExecutable(string pythonFolder)
        {
            var candidates = OperatingSystem.IsWindows()
                ? new[]
                {
                    Path.Combine(pythonFolder, "venv", "Scripts", "python.exe"),
                    "python",
                    "py"
                }
                : new[]
                {
                    Path.Combine(pythonFolder, "venv", "bin", "python"),
                    "python3",
                    "python"
                };

            foreach (var candidate in candidates)
            {
                if (!Path.IsPathRooted(candidate) || System.IO.File.Exists(candidate))
                {
                    return candidate;
                }
            }

            return candidates[0];
        }

        void StartPythonServer()
        {
            if (pythonProcess != null && !pythonProcess.HasExited)
                return;

            pythonLogBuffer.Clear();
            var pythonExe = ResolvePythonExecutable(_pythonFolder);

            if (Path.IsPathRooted(pythonExe) && !System.IO.File.Exists(pythonExe))
                throw new FileNotFoundException($"Khong tim thay Python venv: {pythonExe}");

            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = pythonExe,
                WorkingDirectory = _pythonFolder,
                Arguments = "-m uvicorn FaceID:app --port 8000",
                CreateNoWindow = true,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };

            pythonProcess = Process.Start(psi);

            if (pythonProcess == null)
                throw new InvalidOperationException("Khong the khoi dong Python FaceID process.");

            pythonProcess.OutputDataReceived += (_, e) =>
            {
                if (!string.IsNullOrWhiteSpace(e.Data))
                    pythonLogBuffer.AppendLine(e.Data);
            };
            pythonProcess.ErrorDataReceived += (_, e) =>
            {
                if (!string.IsNullOrWhiteSpace(e.Data))
                    pythonLogBuffer.AppendLine(e.Data);
            };
            pythonProcess.BeginOutputReadLine();
            pythonProcess.BeginErrorReadLine();
        }

        // =========================

        void StopPythonServer()
        {
            try
            {
                if (pythonProcess != null && !pythonProcess.HasExited)
                {
                    pythonProcess.Kill(true);
                    pythonProcess.Dispose();
                    pythonProcess = null;
                }
            }
            catch { }
        }

        // =========================
        // API STATUS
        // =========================

        [HttpGet("status")]
        public async Task<IActionResult> Status()
        {
            try
            {
                await EnsurePythonRunning();

                var res = await client.GetAsync($"{PythonApi}/camera/status");
                var data = await res.Content.ReadAsStringAsync();

                return Content(data, "application/json");
            }
            catch (Exception ex)
            {
                return StatusCode(503, new { message = ex.Message });
            }
        }

        // =========================
        // START CAMERA
        // =========================

        [HttpPost("start")]
        public async Task<IActionResult> StartCamera(string ip)
        {
            try
            {
                await EnsurePythonRunning();

                var encodedIp = Uri.EscapeDataString(ip);
                var res = await client.PostAsync($"{PythonApi}/camera/start?ip_url={encodedIp}", null);
                var data = await res.Content.ReadAsStringAsync();

                return new ContentResult
                {
                    StatusCode = (int)res.StatusCode,
                    Content = data,
                    ContentType = "application/json"
                };
            }
            catch (Exception ex)
            {
                return StatusCode(503, new { message = ex.Message });
            }
        }

        // =========================
        // STOP CAMERA
        // =========================

        [HttpPost("stop")]
        public async Task<IActionResult> StopCamera()
        {
            try
            {
                await EnsurePythonRunning();

                var res = await client.PostAsync($"{PythonApi}/camera/stop", null);
                var data = await res.Content.ReadAsStringAsync();

                return new ContentResult
                {
                    StatusCode = (int)res.StatusCode,
                    Content = data,
                    ContentType = "application/json"
                };
            }
            catch (Exception ex)
            {
                return StatusCode(503, new { message = ex.Message });
            }
        }

        // =========================
        // DISCOVER IP WEBCAM
        // =========================

        [HttpGet("discover-ipwebcam")]
        public async Task<IActionResult> DiscoverIpWebcam(CancellationToken cancellationToken)
        {
            var cameras = await _lanCameraDiscoveryService.DiscoverIpWebcamsAsync(cancellationToken);

            return Ok(new
            {
                count = cameras.Count,
                cameras
            });
        }

        // =========================
        // SHUTDOWN PYTHON SERVER
        // =========================

        [HttpPost("shutdown")]
        public IActionResult ShutdownPython()
        {
            StopPythonServer();

            return Ok(new
            {
                message = "Python server stopped"
            });
        }
    }
}
