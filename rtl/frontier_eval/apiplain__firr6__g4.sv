module apiplain__firr6__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line for past 6 samples (tap[0] = newest = current x)
    reg [7:0] tap [0:5];
    
    // Combinational sum
    reg [15:0] sum;
    
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps and output on reset
            for (k = 0; k < 6; k = k + 1) begin
                tap[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line: oldest (tap[5]) gets replaced,
            // all others shift right
            tap[0] <= x;
            tap[1] <= tap[0];
            tap[2] <= tap[1];
            tap[3] <= tap[2];
            tap[4] <= tap[3];
            tap[5] <= tap[4];
            
            // Compute sum and register output
            y <= sum;
        end
    end
    
    // Compute sum = (1*tap[0] + 2*tap[1] + 3*tap[2] + 4*tap[3] + 5*tap[4] + 6*tap[5])
    always @(*) begin
        sum = ({8'd0, tap[0]}) +           // k=0: coefficient 1
              ({8'd0, tap[1]} + {8'd0, tap[1]}) +  // k=1: coefficient 2
              ({8'd0, tap[2]} + {8'd0, tap[2]} + {8'd0, tap[2]}) +  // k=2: coefficient 3
              ({8'd0, tap[3]} + {8'd0, tap[3]} + {8'd0, tap[3]} + {8'd0, tap[3]}) +  // k=3: coefficient 4
              ({8'd0, tap[4]} + {8'd0, tap[4]} + {8'd0, tap[4]} + {8'd0, tap[4]} + {8'd0, tap[4]}) +  // k=4: coefficient 5
              ({8'd0, tap[5]} + {8'd0, tap[5]} + {8'd0, tap[5]} + {8'd0, tap[5]} + {8'd0, tap[5]} + {8'd0, tap[5]});  // k=5: coefficient 6
    end
    
endmodule