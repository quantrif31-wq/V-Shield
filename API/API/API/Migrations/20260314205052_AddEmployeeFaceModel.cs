using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace API.Migrations
{
    /// <inheritdoc />
    public partial class AddEmployeeFaceModel : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "EmployeeFaceModels",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    EmployeeId = table.Column<int>(type: "int", nullable: false),
                    ModelFileName = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: false),
                    ModelPath = table.Column<string>(type: "nvarchar(500)", maxLength: 500, nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "datetime2", nullable: false, defaultValueSql: "(getdate())")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_EmployeeFaceModels", x => x.Id);
                    table.ForeignKey(
                        name: "FK_EmployeeFaceModel_Employee",
                        column: x => x.EmployeeId,
                        principalTable: "Employee",
                        principalColumn: "EmployeeId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.UpdateData(
                table: "AppUsers",
                keyColumn: "UserId",
                keyValue: 1,
                column: "PasswordHash",
                value: "$2a$11$oEnInEcEn0XgqgvxxXPET.cog8BdP2j2qYginssEkUmA5zx6OdKsy");

            migrationBuilder.CreateIndex(
                name: "IX_EmployeeFaceModels_EmployeeId",
                table: "EmployeeFaceModels",
                column: "EmployeeId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "EmployeeFaceModels");

            migrationBuilder.UpdateData(
                table: "AppUsers",
                keyColumn: "UserId",
                keyValue: 1,
                column: "PasswordHash",
                value: "$2a$11$xELbYg6RNqejwqEdnTUc1eLlHz2NRJ3jAGyerX8P4hZoOgFVLTlLS");
        }
    }
}
