module base__firr26__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap0;
    reg [7:0] tap1;
    reg [7:0] tap2;
    reg [7:0] tap3;
    reg [7:0] tap4;
    reg [7:0] tap5;
    reg [7:0] tap6;
    reg [7:0] tap7;
    reg [7:0] tap8;
    reg [7:0] tap9;
    reg [7:0] tap10;
    reg [7:0] tap11;
    reg [7:0] tap12;
    reg [7:0] tap13;
    reg [7:0] tap14;
    reg [7:0] tap15;
    reg [7:0] tap16;
    reg [7:0] tap17;
    reg [7:0] tap18;
    reg [7:0] tap19;
    reg [7:0] tap20;
    reg [7:0] tap21;
    reg [7:0] tap22;
    reg [7:0] tap23;
    reg [7:0] tap24;
    reg [7:0] tap25;
    
    reg [15:0] acc_sum;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tap0 <= 8'b0;
            tap1 <= 8'b0;
            tap2 <= 8'b0;
            tap3 <= 8'b0;
            tap4 <= 8'b0;
            tap5 <= 8'b0;
            tap6 <= 8'b0;
            tap7 <= 8'b0;
            tap8 <= 8'b0;
            tap9 <= 8'b0;
            tap10 <= 8'b0;
            tap11 <= 8'b0;
            tap12 <= 8'b0;
            tap13 <= 8'b0;
            tap14 <= 8'b0;
            tap15 <= 8'b0;
            tap16 <= 8'b0;
            tap17 <= 8'b0;
            tap18 <= 8'b0;
            tap19 <= 8'b0;
            tap20 <= 8'b0;
            tap21 <= 8'b0;
            tap22 <= 8'b0;
            tap23 <= 8'b0;
            tap24 <= 8'b0;
            tap25 <= 8'b0;
            acc_sum <= 16'b0;
        end else begin
            tap0 <= x;
            tap1 <= tap0;
            tap2 <= tap1;
            tap3 <= tap2;
            tap4 <= tap3;
            tap5 <= tap4;
            tap6 <= tap5;
            tap7 <= tap6;
            tap8 <= tap7;
            tap9 <= tap8;
            tap10 <= tap9;
            tap11 <= tap10;
            tap12 <= tap11;
            tap13 <= tap12;
            tap14 <= tap13;
            tap15 <= tap14;
            tap16 <= tap15;
            tap17 <= tap16;
            tap18 <= tap17;
            tap19 <= tap18;
            tap20 <= tap19;
            tap21 <= tap20;
            tap22 <= tap21;
            tap23 <= tap22;
            tap24 <= tap23;
            tap25 <= tap24;
            
            acc_sum <= 8'b0;
            acc_sum += (8'd1 * tap0);
            acc_sum += (8'd2 * tap1);
            acc_sum += (8'd3 * tap2);
            acc_sum += (8'd4 * tap3);
            acc_sum += (8'd5 * tap4);
            acc_sum += (8'd6 * tap5);
            acc_sum += (8'd7 * tap6);
            acc_sum += (8'd8 * tap7);
            acc_sum += (8'd9 * tap8);
            acc_sum += (8'd10 * tap9);
            acc_sum += (8'd11 * tap10);
            acc_sum += (8'd12 * tap11);
            acc_sum += (8'd13 * tap12);
            acc_sum += (8'd14 * tap13);
            acc_sum += (8'd15 * tap14);
            acc_sum += (8'd16 * tap15);
            acc_sum += (8'd17 * tap16);
            acc_sum += (8'd18 * tap17);
            acc_sum += (8'd19 * tap18);
            acc_sum += (8'd20 * tap19);
            acc_sum += (8'd21 * tap20);
            acc_sum += (8'd22 * tap21);
            acc_sum += (8'd23 * tap22);
            acc_sum += (8'd24 * tap23);
            acc_sum += (8'd25 * tap24);
            acc_sum += (8'd26 * tap25);
            
            y <= acc_sum[15:0];
        end
    end
endmodule