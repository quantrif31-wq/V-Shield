using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;
using System.Text;

namespace API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class BienSoController : ControllerBase
    {
        private static readonly HttpClient client = new HttpClient()
        {
            Timeout = TimeSpan.FromSeconds(5)
        };

        private static Process? pythonProcess;
        private static readonly object lockObj = new object();

        private readonly string pythonApi = "http://127.0.0.1:8001";
        private readonly string pythonFolder = @"C:\DoAnTotNghiep\V-Shield\AI_Project\doc_bien";

        // =========================
        // CHECK PYTHON RUNNING
        // =========================

        async Task<bool> IsPythonRunning()
        {
            try
            {
                var res = await client.GetAsync($"{pythonApi}/status");
                return res.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        // =========================
        // ENSURE PYTHON RUNNING
        // =========================

        async Task EnsurePythonRunning()
        {
            if (await IsPythonRunning())
                return;

            lock (lockObj)
            {
                StartPythonServer();
            }

            for (int i = 0; i < 10; i++)
            {
                await Task.Delay(1000);

                if (await IsPythonRunning())
                    return;
            }

            throw new Exception("Python server failed to start");
        }

        // =========================
        // SAFE CHECK PROCESS
        // =========================

        bool IsProcessAlive()
        {
            try
            {
                if (pythonProcess == null)
                    return false;

                return !pythonProcess.HasExited;
            }
            catch
            {
                return false;
            }
        }

        // =========================
        // START PYTHON
        // =========================

        void StartPythonServer()
        {
            try
            {
                if (IsProcessAlive())
                    return;

                ProcessStartInfo psi = new ProcessStartInfo
                {
                    FileName = "cmd.exe",
                    WorkingDirectory = pythonFolder,
                    Arguments = "/c venv\\Scripts\\activate && uvicorn bienso:app --host 127.0.0.1 --port 8001",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                };

                pythonProcess = new Process();
                pythonProcess.StartInfo = psi;

                pythonProcess.OutputDataReceived += (s, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                        Console.WriteLine("[PYTHON] " + e.Data);
                };

                pythonProcess.ErrorDataReceived += (s, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                        Console.WriteLine("[PYTHON ERROR] " + e.Data);
                };

                pythonProcess.Start();

                pythonProcess.BeginOutputReadLine();
                pythonProcess.BeginErrorReadLine();

                Console.WriteLine("Python server started");
            }
            catch (Exception ex)
            {
                Console.WriteLine("Start python error: " + ex.Message);
            }
        }

        // =========================
        // STOP PYTHON
        // =========================

        void StopPythonServer()
        {
            try
            {
                if (IsProcessAlive())
                {
                    pythonProcess!.Kill(true);
                    pythonProcess.Dispose();
                    pythonProcess = null;
                }
            }
            catch { }
        }

        // =========================
        // STATUS
        // =========================

        [HttpGet("status")]
        public async Task<IActionResult> Status()
        {
            await EnsurePythonRunning();

            var res = await client.GetAsync($"{pythonApi}/status");

            var data = await res.Content.ReadAsStringAsync();

            return Content(data, "application/json");
        }

        // =========================
        // START CAMERA
        // =========================

        [HttpPost("start")]
        public async Task<IActionResult> StartCamera([FromQuery] string ip)
        {
            await EnsurePythonRunning();

            var content = new StringContent(
                $"{{\"ip\":\"{ip}\"}}",
                Encoding.UTF8,
                "application/json"
            );

            var res = await client.PostAsync($"{pythonApi}/start_camera", content);

            var data = await res.Content.ReadAsStringAsync();

            return Content(data, "application/json");
        }

        // =========================
        // STOP CAMERA
        // =========================

        [HttpPost("stop")]
        public async Task<IActionResult> StopCamera()
        {
            // nếu python không chạy thì không làm gì
            if (!IsProcessAlive())
            {
                return Ok(new
                {
                    message = "Python server is not running"
                });
            }

            try
            {
                var res = await client.PostAsync($"{pythonApi}/stop_camera", null);

                var data = await res.Content.ReadAsStringAsync();

                return Content(data, "application/json");
            }
            catch
            {
                return StatusCode(500, new
                {
                    message = "Failed to stop camera"
                });
            }
        }

        // =========================
        // GET PLATE
        // =========================

        [HttpGet("plate")]
        public async Task<IActionResult> GetPlate()
        {
            await EnsurePythonRunning();

            var res = await client.GetAsync($"{pythonApi}/plate");

            var data = await res.Content.ReadAsStringAsync();

            return Content(data, "application/json");
        }

        // =========================
        // SHUTDOWN PYTHON
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