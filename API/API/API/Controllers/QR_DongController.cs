using System.Data;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using API.Data;
using API.Models;
using API.Models.DTOs;
using API.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;

namespace API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class QR_DongController : ControllerBase
    {
        private readonly ApplicationDbContext _context;
        private readonly ILogger<QR_DongController> _logger;
        private readonly string _dynamicQrMasterKey;
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly string _remoteBaseUrl;

        public QR_DongController(
            ApplicationDbContext context,
            ILogger<QR_DongController> logger,
            IConfiguration configuration,
            IHttpClientFactory httpClientFactory,
            IOptions<GateSyncOptions> gateSyncOptions)
        {
            _context = context;
            _logger = logger;
            _httpClientFactory = httpClientFactory;
            _remoteBaseUrl = (gateSyncOptions.Value.RemoteBaseUrl ?? "").TrimEnd('/');
            _dynamicQrMasterKey =
                configuration["DynamicQr:MasterKey"]?.Trim() ??
                configuration["JwtSettings:Secret"]?.Trim() ??
                "VShieldDynamicQrFallbackMasterKey";
        }

        /// <summary>
        /// Tạo QR động hiện tại cho nhân viên.
        /// Lưu ý bảo mật:
        /// - Chỉ trả qrPayload cho FE để render QR
        /// - KHÔNG trả OTP raw ra ngoài ngoài payload QR
        /// </summary>
        [HttpPost("generate")]
        public async Task<IActionResult> GenerateDynamicQr([FromBody] GenerateDynamicQrRequest request)
        {
            if (request == null || request.EmployeeId <= 0)
            {
                return BadRequest(new
                {
                    success = false,
                    message = "EmployeeId không hợp lệ."
                });
            }

            var employee = await _context.Employees
                .FirstOrDefaultAsync(x => x.EmployeeId == request.EmployeeId && x.Status == true);

            if (employee == null)
            {
                return NotFound(new
                {
                    success = false,
                    message = "Không tìm thấy nhân viên hoặc nhân viên đang không hoạt động."
                });
            }

            var dynamicQr = await _context.EmployeeDynamicQrs
                .FirstOrDefaultAsync(x => x.EmployeeId == request.EmployeeId);

            dynamicQr = await EnsureDynamicQrConfigurationAsync(employee, dynamicQr);

            if (!dynamicQr.IsActive)
            {
                return BadRequest(new
                {
                    success = false,
                    message = "QR động của nhân viên này đang bị vô hiệu hóa."
                });
            }

            var utcNow = DateTime.UtcNow;
            var counter = GetCurrentCounter(utcNow, dynamicQr.TimeStepSeconds);
            var otp = GenerateTotp(dynamicQr.SecretKey, counter, dynamicQr.Digits);
            var expiresAtUtc = GetCounterExpiryUtc(utcNow, dynamicQr.TimeStepSeconds);

            // Payload FE dùng để render thành QR image
            var qrPayload = $"EMP:{employee.EmployeeId}|TS:{counter}|OTP:{otp}";

            return Ok(new
            {
                success = true,
                message = "Tạo QR động thành công.",
                data = new
                {
                    employeeId = employee.EmployeeId,
                    employeeName = employee.FullName,
                    qrPayload,
                    timeStepSeconds = dynamicQr.TimeStepSeconds,
                    generatedAtUtc = utcNow,
                    expiresAtUtc,
                    remainingSeconds = (int)Math.Max(0, Math.Floor((expiresAtUtc - utcNow).TotalSeconds))
                }
            });
        }

        /// <summary>
        /// Verify QR động:
        /// 1. Parse payload
        /// 2. Tìm secret của nhân viên
        /// 3. Chỉ chấp nhận đúng counter hiện tại
        /// 4. OTP phải khớp tuyệt đối
        /// 5. KHÔNG chặn quét lặp lại trong cùng time-step
        /// => Miễn còn thời gian hiệu lực thì được dùng nhiều lần
        /// </summary>
        [HttpPost("verify")]
        public async Task<IActionResult> VerifyDynamicQr([FromBody] VerifyDynamicQrRequest request)
        {
            if (request == null || string.IsNullOrWhiteSpace(request.QrPayload))
            {
                return BadRequest(new
                {
                    success = false,
                    message = "QrPayload không được để trống."
                });
            }

            var parseResult = ParseQrPayload(request.QrPayload);
            if (!parseResult.Success)
            {
                await SaveScanLog(null, request.QrPayload, false, parseResult.Message, request.ScannerDevice);

                return BadRequest(new
                {
                    success = false,
                    message = parseResult.Message
                });
            }

            var employeeId = parseResult.EmployeeId!.Value;
            var payloadCounter = parseResult.Counter!.Value;
            var payloadOtp = parseResult.Otp!;

            await using var transaction = await _context.Database.BeginTransactionAsync(IsolationLevel.ReadCommitted);

            try
            {
                var employee = await _context.Employees
                    .FirstOrDefaultAsync(x => x.EmployeeId == employeeId);

                if (employee == null || employee.Status != true)
                {
                    await SaveScanLog(employeeId, request.QrPayload, false,
                        "Nhân viên không hoạt động hoặc không tồn tại.", request.ScannerDevice);

                    await transaction.CommitAsync();

                    return BadRequest(new
                    {
                        success = false,
                        message = "Nhân viên không hoạt động hoặc không tồn tại."
                    });
                }

                var dynamicQr = await _context.EmployeeDynamicQrs
                    .FirstOrDefaultAsync(x => x.EmployeeId == employeeId);

                dynamicQr = await EnsureDynamicQrConfigurationAsync(employee, dynamicQr);

                if (!dynamicQr.IsActive)
                {
                    await SaveScanLog(employeeId, request.QrPayload, false,
                        "QR động của nhân viên đang bị vô hiệu hóa.", request.ScannerDevice);

                    await transaction.CommitAsync();

                    return BadRequest(new
                    {
                        success = false,
                        message = "QR động của nhân viên đang bị vô hiệu hóa."
                    });
                }

                var utcNow = DateTime.UtcNow;
                var currentCounter = GetCurrentCounter(utcNow, dynamicQr.TimeStepSeconds);

                // Chỉ cần QR đang nằm trong đúng time-step hiện tại
                if (payloadCounter != currentCounter)
                {
                    await SaveScanLog(employeeId, request.QrPayload, false,
                        "QR đã hết hạn hoặc chưa đến hiệu lực.", request.ScannerDevice);

                    await transaction.CommitAsync();

                    return BadRequest(new
                    {
                        success = false,
                        message = "QR đã hết hạn hoặc chưa đến hiệu lực."
                    });
                }

                var expectedOtp = GenerateTotp(dynamicQr.SecretKey, currentCounter, dynamicQr.Digits);

                if (!FixedTimeEquals(payloadOtp, expectedOtp))
                {
                    // OTP local không khớp → thử forward verify lên VPS
                    var remoteResult = await TryVerifyViaRemoteAsync(request.QrPayload, request.ScannerDevice);

                    if (remoteResult != null && remoteResult.Success)
                    {
                        // VPS xác nhận OK → ghi scan log thành công vào local
                        await SaveScanLog(employeeId, request.QrPayload, true,
                            "Xác thực QR động thành công (qua VPS).", request.ScannerDevice);

                        dynamicQr.UpdatedAt = DateTime.UtcNow;
                        await _context.SaveChangesAsync();
                        await transaction.CommitAsync();

                        return Ok(new
                        {
                            success = true,
                            message = "Xác thực QR động thành công (qua VPS).",
                            data = new
                            {
                                employeeId = remoteResult.EmployeeId ?? dynamicQr.EmployeeId,
                                employeeName = remoteResult.EmployeeName ?? employee.FullName,
                                verifiedAtUtc = DateTime.UtcNow,
                                counter = currentCounter,
                                expiresAtUtc = GetCounterExpiryUtc(DateTime.UtcNow, dynamicQr.TimeStepSeconds)
                            }
                        });
                    }

                    // VPS cũng thất bại → trả lỗi
                    var failMessage = remoteResult?.Message ?? "QR động không hợp lệ.";

                    await SaveScanLog(employeeId, request.QrPayload, false,
                        failMessage, request.ScannerDevice);

                    await transaction.CommitAsync();

                    return BadRequest(new
                    {
                        success = false,
                        message = failMessage
                    });
                }

                // ĐÃ BỎ CƠ CHẾ:
                // if (dynamicQr.LastUsedCounter.HasValue && dynamicQr.LastUsedCounter.Value == currentCounter)
                // {
                //     return Conflict(... "QR này đã được sử dụng trước đó.")
                // }

                // Có thể vẫn cập nhật thời gian verify gần nhất để audit
                dynamicQr.UpdatedAt = utcNow;

                // Nếu bạn muốn lưu thống kê lần quét gần nhất thì mở lại dòng dưới:
                // dynamicQr.LastUsedCounter = currentCounter;

                await _context.SaveChangesAsync();

                await SaveScanLog(employeeId, request.QrPayload, true,
                    "Xác thực QR động thành công.", request.ScannerDevice);

                await transaction.CommitAsync();

                return Ok(new
                {
                        success = true,
                        message = "Xác thực QR động thành công.",
                        data = new
                        {
                            employeeId = dynamicQr.EmployeeId,
                            employeeName = employee.FullName,
                            verifiedAtUtc = utcNow,
                            counter = currentCounter,
                            expiresAtUtc = GetCounterExpiryUtc(utcNow, dynamicQr.TimeStepSeconds)
                    }
                });
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();

                _logger.LogError(ex, "Lỗi khi verify QR động.");

                await SaveScanLog(employeeId, request.QrPayload, false,
                    "Lỗi hệ thống khi xác thực QR.", request.ScannerDevice);

                return StatusCode(StatusCodes.Status500InternalServerError, new
                {
                    success = false,
                    message = "Lỗi hệ thống khi xác thực QR."
                });
            }
        }

        // =========================
        // REMOTE VERIFY
        // =========================

        private sealed class RemoteVerifyResult
        {
            public bool Success { get; set; }
            public string? Message { get; set; }
            public int? EmployeeId { get; set; }
            public string? EmployeeName { get; set; }
        }

        private async Task<RemoteVerifyResult?> TryVerifyViaRemoteAsync(string qrPayload, string? scannerDevice)
        {
            if (string.IsNullOrWhiteSpace(_remoteBaseUrl))
                return null;

            try
            {
                var client = _httpClientFactory.CreateClient();
                client.Timeout = TimeSpan.FromSeconds(10);

                var requestBody = new
                {
                    qrPayload,
                    scannerDevice
                };

                var json = JsonSerializer.Serialize(requestBody);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                var url = $"{_remoteBaseUrl}/api/QR_Dong/verify";
                _logger.LogInformation("Forwarding QR verify to VPS: {Url}", url);

                var response = await client.PostAsync(url, content);
                var responseBody = await response.Content.ReadAsStringAsync();

                var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                var parsed = JsonSerializer.Deserialize<JsonElement>(responseBody, options);

                var success = parsed.TryGetProperty("success", out var successProp) && successProp.GetBoolean();
                var message = parsed.TryGetProperty("message", out var msgProp) ? msgProp.GetString() : null;

                int? employeeId = null;
                string? employeeName = null;

                if (success && parsed.TryGetProperty("data", out var dataProp))
                {
                    if (dataProp.TryGetProperty("employeeId", out var eidProp))
                        employeeId = eidProp.GetInt32();

                    if (dataProp.TryGetProperty("employeeName", out var enameProp))
                        employeeName = enameProp.GetString();
                }

                _logger.LogInformation(
                    "VPS verify result: success={Success}, message={Message}, employeeId={EmployeeId}",
                    success, message, employeeId);

                return new RemoteVerifyResult
                {
                    Success = success,
                    Message = message,
                    EmployeeId = employeeId,
                    EmployeeName = employeeName
                };
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to forward verify to VPS at {Url}", _remoteBaseUrl);
                return null;
            }
        }

        // =========================
        // HELPER METHODS
        // =========================

        private async Task SaveScanLog(int? employeeId, string qrPayload, bool isValid, string message, string? scannerDevice)
        {
            try
            {
                var log = new DynamicQrScanLog
                {
                    EmployeeId = employeeId ?? 0,
                    QrPayload = qrPayload,
                    IsValid = isValid,
                    Message = message,
                    ScannerDevice = scannerDevice,
                    ScannedAt = DateTime.UtcNow
                };

                _context.DynamicQrScanLogs.Add(log);
                await _context.SaveChangesAsync();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Lỗi khi lưu DynamicQrScanLog");
            }
        }

        private async Task<EmployeeDynamicQr> EnsureDynamicQrConfigurationAsync(
            Employee employee,
            EmployeeDynamicQr? dynamicQr)
        {
            var shouldPersist = false;

            if (dynamicQr == null)
            {
                dynamicQr = new EmployeeDynamicQr
                {
                    EmployeeId = employee.EmployeeId,
                    SecretKey = BuildDeterministicSecret(employee.EmployeeId),
                    TimeStepSeconds = 30,
                    Digits = 6,
                    IsActive = true,
                    CreatedAt = DateTime.UtcNow
                };

                _context.EmployeeDynamicQrs.Add(dynamicQr);
                shouldPersist = true;
            }
            else
            {
                if (string.IsNullOrWhiteSpace(dynamicQr.SecretKey))
                {
                    dynamicQr.SecretKey = BuildDeterministicSecret(employee.EmployeeId);
                    shouldPersist = true;
                }

                if (dynamicQr.TimeStepSeconds <= 0)
                {
                    dynamicQr.TimeStepSeconds = 30;
                    shouldPersist = true;
                }

                if (dynamicQr.Digits <= 0)
                {
                    dynamicQr.Digits = 6;
                    shouldPersist = true;
                }
            }

            if (shouldPersist)
            {
                dynamicQr.UpdatedAt = DateTime.UtcNow;
                await _context.SaveChangesAsync();
            }

            return dynamicQr;
        }

        private static long GetCurrentCounter(DateTime utcNow, int timeStepSeconds)
        {
            var unixTime = new DateTimeOffset(utcNow).ToUnixTimeSeconds();
            return unixTime / timeStepSeconds;
        }

        private static DateTime GetCounterExpiryUtc(DateTime utcNow, int timeStepSeconds)
        {
            var unixTime = new DateTimeOffset(utcNow).ToUnixTimeSeconds();
            var nextBoundary = ((unixTime / timeStepSeconds) + 1) * timeStepSeconds;
            return DateTimeOffset.FromUnixTimeSeconds(nextBoundary).UtcDateTime;
        }

        private static string GenerateTotp(string base32Secret, long counter, int digits = 6)
        {
            var key = Base32Decode(base32Secret);
            var counterBytes = BitConverter.GetBytes(counter);

            if (BitConverter.IsLittleEndian)
                Array.Reverse(counterBytes);

            using var hmac = new HMACSHA1(key);
            var hash = hmac.ComputeHash(counterBytes);

            var offset = hash[^1] & 0x0F;

            int binaryCode =
                ((hash[offset] & 0x7F) << 24) |
                ((hash[offset + 1] & 0xFF) << 16) |
                ((hash[offset + 2] & 0xFF) << 8) |
                (hash[offset + 3] & 0xFF);

            int otp = binaryCode % (int)Math.Pow(10, digits);
            return otp.ToString().PadLeft(digits, '0');
        }

        private static string GenerateBase32Secret(int length = 20)
        {
            var bytes = new byte[length];
            RandomNumberGenerator.Fill(bytes);
            return Base32Encode(bytes);
        }

        private string BuildDeterministicSecret(int employeeId)
        {
            var masterKeyBytes = Encoding.UTF8.GetBytes(_dynamicQrMasterKey);
            var payloadBytes = Encoding.UTF8.GetBytes($"VSHIELD:EMP:{employeeId}");

            using var hmac = new HMACSHA256(masterKeyBytes);
            var hash = hmac.ComputeHash(payloadBytes);
            var secretBytes = hash.Take(20).ToArray();

            return Base32Encode(secretBytes);
        }

        private static (bool Success, int? EmployeeId, long? Counter, string? Otp, string Message) ParseQrPayload(string payload)
        {
            try
            {
                var parts = payload.Split('|', StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length != 3)
                    return (false, null, null, null, "Payload QR không đúng định dạng.");

                var empPart = parts[0].Split(':');
                var tsPart = parts[1].Split(':');
                var otpPart = parts[2].Split(':');

                if (empPart.Length != 2 || tsPart.Length != 2 || otpPart.Length != 2)
                    return (false, null, null, null, "Payload QR không đúng định dạng.");

                if (!empPart[0].Equals("EMP", StringComparison.OrdinalIgnoreCase))
                    return (false, null, null, null, "Thiếu EMP trong payload.");

                if (!tsPart[0].Equals("TS", StringComparison.OrdinalIgnoreCase))
                    return (false, null, null, null, "Thiếu TS trong payload.");

                if (!otpPart[0].Equals("OTP", StringComparison.OrdinalIgnoreCase))
                    return (false, null, null, null, "Thiếu OTP trong payload.");

                if (!int.TryParse(empPart[1], out var employeeId))
                    return (false, null, null, null, "EmployeeId không hợp lệ.");

                if (!long.TryParse(tsPart[1], out var counter))
                    return (false, null, null, null, "Counter không hợp lệ.");

                var otp = otpPart[1]?.Trim();
                if (string.IsNullOrWhiteSpace(otp))
                    return (false, null, null, null, "OTP không hợp lệ.");

                return (true, employeeId, counter, otp, "OK");
            }
            catch
            {
                return (false, null, null, null, "Không thể phân tích payload QR.");
            }
        }

        private static bool FixedTimeEquals(string left, string right)
        {
            if (left == null || right == null)
                return false;

            var leftBytes = Encoding.UTF8.GetBytes(left);
            var rightBytes = Encoding.UTF8.GetBytes(right);

            return leftBytes.Length == rightBytes.Length &&
                   CryptographicOperations.FixedTimeEquals(leftBytes, rightBytes);
        }

        private static string Base32Encode(byte[] data)
        {
            const string alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
            var result = new StringBuilder();

            if (data == null || data.Length == 0)
                return string.Empty;

            int bitBuffer = data[0];
            int currentByte = 1;
            int bitsLeft = 8;

            while (bitsLeft > 0 || currentByte < data.Length)
            {
                if (bitsLeft < 5)
                {
                    if (currentByte < data.Length)
                    {
                        bitBuffer <<= 8;
                        bitBuffer |= data[currentByte++] & 0xFF;
                        bitsLeft += 8;
                    }
                    else
                    {
                        int pad = 5 - bitsLeft;
                        bitBuffer <<= pad;
                        bitsLeft += pad;
                    }
                }

                int index = 0x1F & (bitBuffer >> (bitsLeft - 5));
                bitsLeft -= 5;
                result.Append(alphabet[index]);
            }

            return result.ToString();
        }

        private static byte[] Base32Decode(string input)
        {
            const string alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";

            input = input.Trim().TrimEnd('=').ToUpperInvariant();

            var output = new List<byte>();
            int bitBuffer = 0;
            int bitsLeft = 0;

            foreach (char c in input)
            {
                int val = alphabet.IndexOf(c);
                if (val < 0)
                    throw new FormatException("SecretKey Base32 không hợp lệ.");

                bitBuffer <<= 5;
                bitBuffer |= val & 0x1F;
                bitsLeft += 5;

                if (bitsLeft >= 8)
                {
                    output.Add((byte)(bitBuffer >> (bitsLeft - 8)));
                    bitsLeft -= 8;
                }
            }

            return output.ToArray();
        }
    }
}
