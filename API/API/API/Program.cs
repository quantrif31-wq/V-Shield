using System.Security.Claims;
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

            builder.Services.AddDbContext<ApplicationDbContext>(options =>
                options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

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
                    IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey)),
                    NameClaimType = System.IdentityModel.Tokens.Jwt.JwtRegisteredClaimNames.UniqueName,
                    RoleClaimType = ClaimTypes.Role
                };
            });

            builder.Services.AddAuthorization();

            builder.Services.AddMemoryCache();
            builder.Services.AddScoped<IAuthService, AuthService>();
            builder.Services.AddScoped<IVehicleService, VehicleService>();
            builder.Services.AddScoped<ILanCameraDiscoveryService, LanCameraDiscoveryService>();
            builder.Services.AddHttpClient();
            builder.Services.AddSignalR();
            builder.Services.AddControllers();

            builder.Services.AddEndpointsApiExplorer();
            builder.Services.AddSwaggerGen(c =>
            {
                c.SwaggerDoc("v1", new OpenApiInfo
                {
                    Title = "V-Shield API",
                    Version = "v1",
                    Description = "API quan ly he thong V-Shield voi phan quyen Admin/Staff/BaoVe"
                });

                c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
                {
                    Name = "Authorization",
                    Type = SecuritySchemeType.Http,
                    Scheme = "bearer",
                    BearerFormat = "JWT",
                    In = ParameterLocation.Header,
                    Description = "Nhap JWT token. Vi du: Bearer {token}"
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
            EnsureSeedAdmin(app.Services, builder.Configuration);

            if (app.Environment.IsDevelopment())
            {
                app.UseSwagger();
                app.UseSwaggerUI();
            }

            // app.UseHttpsRedirection();
            app.UseStaticFiles();
            app.UseCors("AllowVue");
            app.UseAuthentication();
            app.UseAuthorization();

            app.MapControllers();
            app.MapHub<EmployeeStatsHub>("/hubs/employee-stats");

            app.Run();
        }

        private static void EnsureSeedAdmin(IServiceProvider services, IConfiguration configuration)
        {
            using var scope = services.CreateScope();
            var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();

            db.Database.Migrate();

            var seedSection = configuration.GetSection("SeedAdmin");
            var adminUsername = (seedSection["Username"] ?? "admin").Trim();
            var adminPassword = seedSection["Password"] ?? "Admin@123";
            var adminFullName = seedSection["FullName"] ?? "Quan tri vien";
            var resetPasswordOnStartup = seedSection.GetValue("ResetPasswordOnStartup", false);
            var normalizedAdminUsername = NormalizeUsername(adminUsername);

            var adminUser = db.AppUsers.FirstOrDefault(u =>
                u.Username.Trim().ToUpper() == normalizedAdminUsername);

            if (adminUser == null)
            {
                if (!db.AppUsers.Any())
                {
                    // Only reseed when the table is empty so existing IDs are not disturbed.
                    db.Database.ExecuteSqlRaw("DBCC CHECKIDENT ('AppUsers', RESEED, 0)");
                }

                db.AppUsers.Add(new AppUser
                {
                    Username = adminUsername,
                    PasswordHash = BCrypt.Net.BCrypt.HashPassword(adminPassword),
                    FullName = adminFullName,
                    Role = "Admin",
                    IsActive = true,
                    CreatedAt = DateTime.UtcNow,
                    EmployeeId = null
                });

                db.SaveChanges();
                return;
            }

            var hasChanges = false;

            if (!string.Equals(adminUser.Username, adminUsername, StringComparison.Ordinal))
            {
                adminUser.Username = adminUsername;
                hasChanges = true;
            }

            if (!string.Equals(adminUser.Role, "Admin", StringComparison.OrdinalIgnoreCase))
            {
                adminUser.Role = "Admin";
                hasChanges = true;
            }

            if (!adminUser.IsActive)
            {
                adminUser.IsActive = true;
                hasChanges = true;
            }

            if (string.IsNullOrWhiteSpace(adminUser.FullName))
            {
                adminUser.FullName = adminFullName;
                hasChanges = true;
            }

            if (resetPasswordOnStartup && !BCrypt.Net.BCrypt.Verify(adminPassword, adminUser.PasswordHash))
            {
                adminUser.PasswordHash = BCrypt.Net.BCrypt.HashPassword(adminPassword);
                hasChanges = true;
            }

            if (hasChanges)
            {
                db.SaveChanges();
            }
        }

        private static string NormalizeUsername(string username) =>
            username.Trim().ToUpperInvariant();
    }
}
