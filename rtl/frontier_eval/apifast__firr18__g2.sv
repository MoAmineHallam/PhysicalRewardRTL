module apifast__firr18__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

// -------------------------------------------------------
// 1. Delay line (registered)
// -------------------------------------------------------
reg [7:0] tap [0:17];     // tap[0] = newest sample

integer i;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 18; i = i + 1)
            tap[i] <= 8'd0;
    end else begin
        // Shift: new x becomes tap[0], old tap[0] -> tap[1], etc.
        tap[0] <= x;
        for (i = 1; i < 18; i = i + 1)
            tap[i] <= tap[i-1];
    end
end

// -------------------------------------------------------
// 2. Pipelined multiply-add tree (18 taps -> 1 result)
// -------------------------------------------------------
// Stage 0: multiply each tap by coefficient (k+1)
// Coefficient (k+1) * tap[k] → up to 8+5=13 bits (unsigned)
// We'll keep full precision: 13-bit products
wire [12:0] prod [0:17];
genvar k;
generate
    for (k = 0; k < 18; k = k + 1) begin : gen_mul
        // k+1 ranges 1..18 (5 bits), product max 255*18 = 4590 (13 bits)
        assign prod[k] = tap[k] * (k+1);
    end
endgenerate

// -------------------------------------------------------
// 3. Pipeline registers for adder tree
// -------------------------------------------------------
// We'll build a balanced binary tree with pipeline registers
// between stages to keep each stage minimal (one adder per node)
// Number of stages: ceil(log2(18)) = 5 stages (since 2^5=32 > 18)
// We'll use a recursive pipeline approach: for each level, we halve the number of values

// Stage 1: 9 sums (18 -> 9)
reg [13:0] s1 [0:8];   // 13-bit + 13-bit → 14 bits max
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 9; i = i + 1)
            s1[i] <= 14'd0;
    end else begin
        for (i = 0; i < 9; i = i + 1)
            s1[i] <= prod[2*i] + prod[2*i+1];
    end
end

// Stage 2: 5 sums (9 -> 5) — last sum is just s1[8] (odd one out)
reg [14:0] s2 [0:4];   // 14-bit + 14-bit → 15 bits
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 5; i = i + 1)
            s2[i] <= 15'd0;
    end else begin
        for (i = 0; i < 4; i = i + 1)
            s2[i] <= s1[2*i] + s1[2*i+1];
        s2[4] <= s1[8];  // leftover
    end
end

// Stage 3: 3 sums (5 -> 3)
reg [15:0] s3 [0:2];   // 15-bit + 15-bit → 16 bits
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 3; i = i + 1)
            s3[i] <= 16'd0;
    end else begin
        s3[0] <= s2[0] + s2[1];
        s3[1] <= s2[2] + s2[3];
        s3[2] <= s2[4];
    end
end

// Stage 4: 2 sums (3 -> 2)
reg [16:0] s4 [0:1];   // 16-bit + 16-bit → 17 bits
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        s4[0] <= 17'd0;
        s4[1] <= 17'd0;
    end else begin
        s4[0] <= s3[0] + s3[1];
        s4[1] <= s3[2];
    end
end

// Stage 5: final sum (2 -> 1)
reg [17:0] sum_full;    // 17-bit + 17-bit → 18 bits
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        sum_full <= 18'd0;
    else
        sum_full <= s4[0] + s4[1];
end

// -------------------------------------------------------
// 4. Output: low 16 bits of the final sum
// -------------------------------------------------------
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        y <= 16'd0;
    else
        y <= sum_full[15:0];
end

endmodule