using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;
using System.Net.Http;
using System.Threading.Tasks;

namespace API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class FaceIDController : ControllerBase
    {
        private static readonly HttpClient client = new HttpClient();

        string pythonApi = "http://127.0.0.1:8000";
        string pythonFolder = @"C:\DoAnTotNghiep\V-Shield\AI_Project\face_recognition";

        async Task EnsurePythonRunning()
        {
            try
            {
                var res = await client.GetAsync($"{pythonApi}/");
                if (res.IsSuccessStatusCode)
                    return;
            }
            catch { }

            StartPythonServer();

            await Task.Delay(3000);
        }

        void StartPythonServer()
        {
            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = "cmd.exe",
                WorkingDirectory = pythonFolder,
                Arguments = "/c venv\\Scripts\\activate && uvicorn FaceID:app --port 8000",
                CreateNoWindow = true,
                UseShellExecute = false
            };

            Process.Start(psi);
        }

        // =========================

        [HttpGet("status")]
        public async Task<IActionResult> Status()
        {
            await EnsurePythonRunning();

            var res = await client.GetAsync($"{pythonApi}/camera/status");
            var data = await res.Content.ReadAsStringAsync();

            return Content(data, "application/json");
        }

        // =========================

        [HttpPost("start")]
        public async Task<IActionResult> StartCamera(string ip)
        {
            await EnsurePythonRunning();

            var res = await client.PostAsync($"{pythonApi}/camera/start?ip_url={ip}", null);
            var data = await res.Content.ReadAsStringAsync();

            return Content(data, "application/json");
        }

        // =========================

        [HttpPost("stop")]
        public async Task<IActionResult> StopCamera()
        {
            await EnsurePythonRunning();

            var res = await client.PostAsync($"{pythonApi}/camera/stop", null);
            var data = await res.Content.ReadAsStringAsync();

            return Content(data, "application/json");
        }
    }
}