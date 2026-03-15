using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace API.Migrations
{
    /// <inheritdoc />
    public partial class AddVehicleParkingStatus : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "ParkingStatus",
                table: "Vehicle",
                type: "nvarchar(10)",
                maxLength: 10,
                nullable: false,
                defaultValue: "OUT");

            migrationBuilder.UpdateData(
                table: "AppUsers",
                keyColumn: "UserId",
                keyValue: 1,
                column: "PasswordHash",
                value: "$2a$11$3u1MjpEbkPc4kdZGmYUAWe48S2shbpWxLZIPga5ildrJXKeqOXtGG");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "ParkingStatus",
                table: "Vehicle");

            migrationBuilder.UpdateData(
                table: "AppUsers",
                keyColumn: "UserId",
                keyValue: 1,
                column: "PasswordHash",
                value: "$2a$11$oEnInEcEn0XgqgvxxXPET.cog8BdP2j2qYginssEkUmA5zx6OdKsy");
        }
    }
}
