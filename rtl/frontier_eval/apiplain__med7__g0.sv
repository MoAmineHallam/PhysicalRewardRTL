module apiplain__med7__g0 (
  input clk,
  input rst_n,
  input [7:0] x,
  output reg [15:0] y
);
  reg [7:0] shift_reg [0:6];  // 7-sample window, shift register
  wire [7:0] s0, s1, s2, s3, s4, s5, s6;
  wire [7:0] m1, m2, m3, m4, m5, m6, m7;
  
  integer i;
  
  // Shift register: load new sample and shift old ones
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (i = 0; i < 7; i = i + 1)
        shift_reg[i] <= 8'd0;
    end else begin
      shift_reg[0] <= x;
      for (i = 1; i < 7; i = i + 1)
        shift_reg[i] <= shift_reg[i-1];
    end
  end
  
  // Assign wires for readability
  assign s0 = shift_reg[0];
  assign s1 = shift_reg[1];
  assign s2 = shift_reg[2];
  assign s3 = shift_reg[3];
  assign s4 = shift_reg[4];
  assign s5 = shift_reg[5];
  assign s6 = shift_reg[6];
  
  // Stage 1: compare all pairs to get low and high values
  // For 7 numbers, we need ceil(log2(7)) = 3 comparison layers.
  
  // Pair 0: (s0,s1), Pair 1: (s2,s3), Pair 2: (s4,s5); s6 waits
  wire [7:0] p0_low, p0_high, p1_low, p1_high, p2_low, p2_high;
  
  assign p0_low  = (s0 < s1) ? s0 : s1;
  assign p0_high = (s0 < s1) ? s1 : s0;
  assign p1_low  = (s2 < s3) ? s2 : s3;
  assign p1_high = (s3 < s2) ? s2 : s3;
  assign p2_low  = (s4 < s5) ? s4 : s5;
  assign p2_high = (s5 < s4) ? s4 : s5;
  
  // Stage 2: compare across triples and one additional
  // We'll find the median by sorting network for 7 elements.
  // Full odd-even sort network for 7 elements using compare-swap.
  
  // We'll use a flattening approach: implement Batcher's odd-even mergesort
  // for n=7. This requires 16 comparators.
  
  reg [7:0] a1, a2, a3, a4, a5, a6, a7;
  wire [7:0] b1, b2, b3, b4, b5, b6, b7;
  
  // Initial copy
  always @(*) begin
    a1 = s0; a2 = s1; a3 = s2; a4 = s3; a5 = s4; a6 = s5; a7 = s6;
  end
  
  // Compare-swap functions
  function [15:0] cswap;
    input [7:0] x, y;
    begin
      cswap = (x < y) ? {x, y} : {y, x};
    end
  endfunction
  
  // Odd-even sort network for 7 elements
  // Layer 1: compare (1,2) (3,4) (5,6)
  wire [7:0] l1_1, l1_2, l1_3, l1_4, l1_5, l1_6, l1_7;
  assign {l1_1, l1_2} = cswap(a1, a2);
  assign {l1_3, l1_4} = cswap(a3, a4);
  assign {l1_5, l1_6} = cswap(a5, a6);
  assign l1_7 = a7;
  
  // Layer 2: compare (2,3) (4,5) (6,7)
  wire [7:0] l2_1, l2_2, l2_3, l2_4, l2_5, l2_6, l2_7;
  assign l2_1 = l1_1;
  assign {l2_2, l2_3} = cswap(l1_2, l1_3);
  assign {l2_4, l2_5} = cswap(l1_4, l1_5);
  assign {l2_6, l2_7} = cswap(l1_6, l1_7);
  
  // Layer 3: compare (1,2) (3,4) (5,6)
  wire [7:0] l3_1, l3_2, l3_3, l3_4, l3_5, l3_6, l3_7;
  assign {l3_1, l3_2} = cswap(l2_1, l2_2);
  assign {l3_3, l3_4} = cswap(l2_3, l2_4);
  assign {l3_5, l3_6} = cswap(l2_5, l2_6);
  assign l3_7 = l2_7;
  
  // Layer 4: compare (2,3) (4,5) (6,7)
  wire [7:0] l4_1, l4_2, l4_3, l4_4, l4_5, l4_6, l4_7;
  assign l4_1 = l3_1;
  assign {l4_2, l4_3} = cswap(l3_2, l3_3);
  assign {l4_4, l4_5} = cswap(l3_4, l3_5);
  assign {l4_6, l4_7} = cswap(l3_6, l3_7);
  
  // Layer 5: compare (1,2) (3,4) (5,6)
  wire [7:0] l5_1, l5_2, l5_3, l5_4, l5_5, l5_6, l5_7;
  assign {l5_1, l5_2} = cswap(l4_1, l4_2);
  assign {l5_3, l5_4} = cswap(l4_3, l4_4);
  assign {l5_5, l5_6} = cswap(l4_5, l4_6);
  assign l5_7 = l4_7;
  
  // Layer 6: compare (2,3) (4,5)
  wire [7:0] l6_1, l6_2, l6_3, l6_4, l6_5, l6_6, l6_7;
  assign l6_1 = l5_1;
  assign {l6_2, l6_3} = cswap(l5_2, l5_3);
  assign {l6_4, l6_5} = cswap(l5_4, l5_5);
  assign l6_6 = l5_6;
  assign l6_7 = l5_7;
  
  // Layer 7: compare (3,4)
  wire [7:0] l7_1, l7_2, l7_3, l7_4, l7_5, l7_6, l7_7;
  assign l7_1 = l6_1;
  assign l7_2 = l6_2;
  assign {l7_3, l7_4} = cswap(l6_3, l6_4);
  assign l7_5 = l6_5;
  assign l7_6 = l6_6;
  assign l7_7 = l6_7;
  
  // The median is the 4th element (index 3)
  wire [7:0] median = l7_4;
  
  // Registered output with zero-extension to 16 bits
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      y <= 16'd0;
    else
      y <= {8'd0, median};
  end
  
endmodule