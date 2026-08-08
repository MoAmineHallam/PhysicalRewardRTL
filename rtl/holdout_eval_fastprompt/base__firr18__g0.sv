module base__firr18__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap [17:0];
    reg [15:0] sum;
    
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'b0;
            sum <= 16'b0;
            for (k = 0; k < 18; k = k + 1) begin
                tap[k] <= 8'b0;
            end
        end
        else begin
            // shift in new sample
            tap[0] <= x;
            
            // update sum
            sum <= {14'b0, tap[0]}*(8'd1)
                 + {14'b0, tap[1]}*(8'd2)
                 + {14'b0, tap[2]}*(8'd3)
                 + {14'b0, tap[3]}*(8'd4)
                 + {14'b0, tap[4]}*(8'd5)
                 + {14'b0, tap[5]}*(8'd6)
                 + {14'b0, tap[6]}*(8'd7)
                 + {14'b0, tap[7]}*(8'd8)
                 + {14'b0, tap[8]}*(8'd9)
                 + {14'b0, tap[9]}*(8'd10)
                 + {14'b0, tap[10]}*(8'd11)
                 + {14'b0, tap[11]}*(8'd12)
                 + {14'b0, tap[12]}*(8'd13)
                 + {14'b0, tap[13]}*(8'd14)
                 + {14'b0, tap[14]}*(8'd15)
                 + {14'b0, tap[15]}*(8'd16)
                 + {14'b0, tap[16]}*(8'd17)
                 + {14'b0, tap[17]}*(8'd18);
            
            // shift all taps
            for (k = 17; k > 0; k = k - 1) begin
                tap[k] <= tap[k-1];
            end
            
            // output low 16 bits of sum
            y <= sum[15:0];
        end
    end

endmodule