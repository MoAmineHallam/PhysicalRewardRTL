module base__fir6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg  [7:0] delay_line [0:5];
    reg  [15:0] acc;
    
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
            acc <= 0;
            for (int i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 0;
            end
        end else begin
            delay_line[0] <= x;
            delay_line[1] <= delay_line[0];
            delay_line[2] <= delay_line[1];
            delay_line[3] <= delay_line[2];
            delay_line[4] <= delay_line[3];
            delay_line[5] <= delay_line[4];
            
            acc <= {8'b0, x} * 8'd3 + {8'b0, delay_line[0]} * 8'd5 + {8'b0, delay_line[1]} * 8'd7 + {8'b0, delay_line[2]} * 8'd7 + {8'b0, delay_line[3]} * 8'd5 + {8'b0, delay_line[4]} * 8'd3;
            
            y <= acc;
        end
    end

endmodule