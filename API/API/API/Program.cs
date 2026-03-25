using System.Text;
using API.Data;
using API.Hubs;
using API.Models;
using API.Services;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;

namespace API
{
    public class Program
    {
        public static void Main(string[] args)
        {
            var builder = WebApplication.CreateBuilder(args);

            // ── Database ──────────────────────────────────────────────────────────
            builder.Services.AddDbContext<ApplicationDbContext>(options =>
                options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

            // ── JWT Authentication ────────────────────────────────────────────────
            var jwtSettings = builder.Configuration.GetSection("JwtSettings");
            var secretKey = jwtSettings["Secret"]!;

            builder.Services.AddAuthentication(options =>
            {
                options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
                options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
            })
            .AddJwtBearer(options =>
            {
                options.TokenValidationParameters = new TokenValidationParameters
                {
                    ValidateIssuer = true,
                    ValidateAudience = true,
                    ValidateLifetime = true,
                    ValidateIssuerSigningKey = true,
                    ValidIssuer = jwtSettings["Issuer"],
                    ValidAudience = jwtSettings["Audience"],
                    IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey))
                };
            });

            builder.Services.AddAuthorization();

            // ── Application Services ──────────────────────────────────────────────
            builder.Services.AddMemoryCache();
            builder.Services.AddScoped<IAuthService, AuthService>();
            builder.Services.AddScoped<IVehicleService, VehicleService>();
            builder.Services.AddScoped<ILanCameraDiscoveryService, LanCameraDiscoveryService>();
            builder.Services.AddHttpClient();
            // ── SignalR ───────────────────────────────────────────────────────────
            builder.Services.AddSignalR();

            // ── Controllers ───────────────────────────────────────────────────────
            builder.Services.AddControllers();

            // ── Swagger với hỗ trợ Bearer Token ──────────────────────────────────
            builder.Services.AddEndpointsApiExplorer();
            builder.Services.AddSwaggerGen(c =>
            {
                c.SwaggerDoc("v1", new OpenApiInfo
                {
                    Title = "V-Shield API",
                    Version = "v1",
                    Description = "API quản lý hệ thống V-Shield với phân quyền Admin/Staff/BaoVe"
                });

                // Thêm nút Authorize trên Swagger UI
                c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
                {
                    Name = "Authorization",
                    Type = SecuritySchemeType.Http,
                    Scheme = "bearer",
                    BearerFormat = "JWT",
                    In = ParameterLocation.Header,
                    Description = "Nhập JWT token. Ví dụ: Bearer {token}"
                });

                c.AddSecurityRequirement(new OpenApiSecurityRequirement
                {
                    {
                        new OpenApiSecurityScheme
                        {
                            Reference = new OpenApiReference
                            {
                                Type = ReferenceType.SecurityScheme,
                                Id = "Bearer"
                            }
                        },
                        Array.Empty<string>()
                    }
                });
            });

            // ── CORS (cho phép Vue.js gọi) ────────────────────────────────────────
            builder.Services.AddCors(options =>
            {
                var configuredOrigins = builder.Configuration.GetSection("AppSettings:AllowedOrigins").Get<string[]>() ?? Array.Empty<string>();
                var frontendUrl = builder.Configuration["AppSettings:FrontendUrl"];
                var allowedOrigins = configuredOrigins
                    .Append(frontendUrl ?? string.Empty)
                    .Where(origin => !string.IsNullOrWhiteSpace(origin))
                    .Select(origin => origin.Trim().TrimEnd('/'))
                    .Distinct(StringComparer.OrdinalIgnoreCase)
                    .ToArray();

                if (allowedOrigins.Length == 0)
                {
                    allowedOrigins = new[]
                    {
                        "http://localhost:5173",
                        "http://localhost:5174",
                        "http://localhost:5175"
                    };
                }

                options.AddPolicy("AllowVue", policy =>
                {
                    policy
                        .WithOrigins(allowedOrigins)
                        .AllowAnyHeader()
                        .AllowAnyMethod()
                        .AllowCredentials();
                });
            });

            var app = builder.Build();
            using (var scope = app.Services.CreateScope())
            {
                var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
                db.Database.Migrate();

                if (!db.AppUsers.Any(u => u.Username == "admin"))
                {
                    // Reset IDENTITY về 0 trước khi seed để admin luôn là UserId = 1
                    db.Database.ExecuteSqlRaw("DBCC CHECKIDENT ('AppUsers', RESEED, 0)");

                    db.AppUsers.Add(new AppUser
                    {
                        Username = "admin",
                        PasswordHash = BCrypt.Net.BCrypt.HashPassword("Admin@123"),
                        FullName = "Quản trị viên",
                        Role = "Admin",
                        IsActive = true,
                        CreatedAt = DateTime.UtcNow,
                        EmployeeId = null
                    });
                    db.SaveChanges();
                }
            }

            // ── HTTP Pipeline ─────────────────────────────────────────────────────
            if (app.Environment.IsDevelopment())
            {
                app.UseSwagger();
                app.UseSwaggerUI();
            }

            // app.UseHttpsRedirection();
            app.UseStaticFiles(); // Serve files từ wwwroot/
            app.UseCors("AllowVue");

            // Authentication PHẢI trước Authorization
            app.UseAuthentication();
            app.UseAuthorization();

            app.MapControllers();

            // ── SignalR Hub ───────────────────────────────────────────────────────
            app.MapHub<EmployeeStatsHub>("/hubs/employee-stats");

            app.Run();
        }
    }
}
