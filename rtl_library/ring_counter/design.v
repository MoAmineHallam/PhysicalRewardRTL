// 4-bit ring counter. Resets to 4'b0001, rotates left each cycle.
// No external inputs. Period = 4.
module ring_counter (
    input  wire       clk,
    input  wire       rst_n,
    output reg  [3:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 4'b0001;
        else        count <= {count[2:0], count[3]};
    end
endmodule
