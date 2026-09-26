// calc: read `<a> <op> <b>` from stdin, print the result.
// Reference implementation; written against zig 0.13/0.14 std.
const std = @import("std");

pub fn main() !void {
    var buf: [64]u8 = undefined;
    const stdin = std.io.getStdIn().reader();
    const line = (try stdin.readUntilDelimiterOrEof(&buf, '\n')) orelse "";
    var it = std.mem.tokenizeScalar(u8, line, ' ');
    const a = try std.fmt.parseInt(i64, it.next() orelse return error.BadInput, 10);
    const op = (it.next() orelse return error.BadInput)[0];
    const b = try std.fmt.parseInt(i64, it.next() orelse return error.BadInput, 10);
    const r: i64 = switch (op) {
        '+' => a + b,
        '-' => a - b,
        '*' => a * b,
        else => return error.BadOp,
    };
    try std.io.getStdOut().writer().print("{d}\n", .{r});
}
