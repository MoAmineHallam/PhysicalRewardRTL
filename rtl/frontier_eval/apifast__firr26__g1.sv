module apifast__firr26__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // -----------------------------------------------------------------
    // 26-tap direct-form FIR filter
    // coefficients: c[k] = k+1, for k = 0..25
    // tap[0] = newest sample = x
    // tap[25] = oldest sample
    //
    // Pipeline strategy:
    //   Stage 0: shift delay line, compute 26 products (each k+1 * tap[k])
    //   Stage 1: sum pairs (13 sums)
    //   Stage 2: sum pairs -> 7 sums
    //   Stage 3: sum pairs -> 4 sums
    //   Stage 4: sum pairs -> 2 sums
    //   Stage 5: final sum -> y (registered)
    // -----------------------------------------------------------------

    // ---------------------------------------------------------------
    // Delay line (registered)
    // ---------------------------------------------------------------
    reg [7:0] tap0, tap1, tap2, tap3, tap4, tap5, tap6, tap7;
    reg [7:0] tap8, tap9, tap10, tap11, tap12, tap13, tap14, tap15;
    reg [7:0] tap16, tap17, tap18, tap19, tap20, tap21, tap22, tap23;
    reg [7:0] tap24, tap25;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tap0  <= 8'd0; tap1  <= 8'd0; tap2  <= 8'd0; tap3  <= 8'd0;
            tap4  <= 8'd0; tap5  <= 8'd0; tap6  <= 8'd0; tap7  <= 8'd0;
            tap8  <= 8'd0; tap9  <= 8'd0; tap10 <= 8'd0; tap11 <= 8'd0;
            tap12 <= 8'd0; tap13 <= 8'd0; tap14 <= 8'd0; tap15 <= 8'd0;
            tap16 <= 8'd0; tap17 <= 8'd0; tap18 <= 8'd0; tap19 <= 8'd0;
            tap20 <= 8'd0; tap21 <= 8'd0; tap22 <= 8'd0; tap23 <= 8'd0;
            tap24 <= 8'd0; tap25 <= 8'd0;
        end else begin
            // shift: oldest out, new x in
            tap25 <= tap24;
            tap24 <= tap23;
            tap23 <= tap22;
            tap22 <= tap21;
            tap21 <= tap20;
            tap20 <= tap19;
            tap19 <= tap18;
            tap18 <= tap17;
            tap17 <= tap16;
            tap16 <= tap15;
            tap15 <= tap14;
            tap14 <= tap13;
            tap13 <= tap12;
            tap12 <= tap11;
            tap11 <= tap10;
            tap10 <= tap9;
            tap9  <= tap8;
            tap8  <= tap7;
            tap7  <= tap6;
            tap6  <= tap5;
            tap5  <= tap4;
            tap4  <= tap3;
            tap3  <= tap2;
            tap2  <= tap1;
            tap1  <= tap0;
            tap0  <= x;
        end
    end

    // ---------------------------------------------------------------
    // Pipeline stage 0: compute all 26 products (k+1)*tap[k]
    // coefficients: 1..26
    // product width: 8-bit * up to 26 (5 bits) -> max 13 bits -> safe 16-bit
    // ---------------------------------------------------------------
    reg [15:0] p0,  p1,  p2,  p3,  p4,  p5,  p6,  p7;
    reg [15:0] p8,  p9,  p10, p11, p12, p13, p14, p15;
    reg [15:0] p16, p17, p18, p19, p20, p21, p22, p23;
    reg [15:0] p24, p25;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p0  <= 16'd0; p1  <= 16'd0; p2  <= 16'd0; p3  <= 16'd0;
            p4  <= 16'd0; p5  <= 16'd0; p6  <= 16'd0; p7  <= 16'd0;
            p8  <= 16'd0; p9  <= 16'd0; p10 <= 16'd0; p11 <= 16'd0;
            p12 <= 16'd0; p13 <= 16'd0; p14 <= 16'd0; p15 <= 16'd0;
            p16 <= 16'd0; p17 <= 16'd0; p18 <= 16'd0; p19 <= 16'd0;
            p20 <= 16'd0; p21 <= 16'd0; p22 <= 16'd0; p23 <= 16'd0;
            p24 <= 16'd0; p25 <= 16'd0;
        end else begin
            p0  <= 16'(1  * tap0);
            p1  <= 16'(2  * tap1);
            p2  <= 16'(3  * tap2);
            p3  <= 16'(4  * tap3);
            p4  <= 16'(5  * tap4);
            p5  <= 16'(6  * tap5);
            p6  <= 16'(7  * tap6);
            p7  <= 16'(8  * tap7);
            p8  <= 16'(9  * tap8);
            p9  <= 16'(10 * tap9);
            p10 <= 16'(11 * tap10);
            p11 <= 16'(12 * tap11);
            p12 <= 16'(13 * tap12);
            p13 <= 16'(14 * tap13);
            p14 <= 16'(15 * tap14);
            p15 <= 16'(16 * tap15);
            p16 <= 16'(17 * tap16);
            p17 <= 16'(18 * tap17);
            p18 <= 16'(19 * tap18);
            p19 <= 16'(20 * tap19);
            p20 <= 16'(21 * tap20);
            p21 <= 16'(22 * tap21);
            p22 <= 16'(23 * tap22);
            p23 <= 16'(24 * tap23);
            p24 <= 16'(25 * tap24);
            p25 <= 16'(26 * tap25);
        end
    end

    // ---------------------------------------------------------------
    // Pipeline stage 1: sum pairs (13 sums: s0..s12)
    // ---------------------------------------------------------------
    reg [15:0] s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0 <= 16'd0; s1 <= 16'd0; s2 <= 16'd0; s3 <= 16'd0;
            s4 <= 16'd0; s5 <= 16'd0; s6 <= 16'd0; s7 <= 16'd0;
            s8 <= 16'd0; s9 <= 16'd0; s10 <= 16'd0; s11 <= 16'd0;
            s12 <= 16'd0;
        end else begin
            s0  <= p0  + p1;
            s1  <= p2  + p3;
            s2  <= p4  + p5;
            s3  <= p6  + p7;
            s4  <= p8  + p9;
            s5  <= p10 + p11;
            s6  <= p12 + p13;
            s7  <= p14 + p15;
            s8  <= p16 + p17;
            s9  <= p18 + p19;
            s10 <= p20 + p21;
            s11 <= p22 + p23;
            s12 <= p24 + p25;
        end
    end

    // ---------------------------------------------------------------
    // Pipeline stage 2: sum pairs -> 7 sums (t0..t6)
    // t0 = s0+s1, t1=s2+s3, t2=s4+s5, t3=s6+s7, t4=s8+s9, t5=s10+s11
    // t6 = s12 (odd one)
    // ---------------------------------------------------------------
    reg [15:0] t0, t1, t2, t3, t4, t5, t6;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            t0 <= 16'd0; t1 <= 16'd0; t2 <= 16'd0; t3 <= 16'd0;
            t4 <= 16'd0; t5 <= 16'd0; t6 <= 16'd0;
        end else begin
            t0 <= s0 + s1;
            t1 <= s2 + s3;
            t2 <= s4 + s5;
            t3 <= s6 + s7;
            t4 <= s8 + s9;
            t5 <= s10 + s11;
            t6 <= s12;
        end
    end

    // ---------------------------------------------------------------
    // Pipeline stage 3: sum pairs -> 4 sums (u0..u3)
    // u0=t0+t1, u1=t2+t3, u2=t4+t5, u3=t6
    // ---------------------------------------------------------------
    reg [15:0] u0, u1, u2, u3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            u0 <= 16'd0; u1 <= 16'd0; u2 <= 16'd0; u3 <= 16'd0;
        end else begin
            u0 <= t0 + t1;
            u1 <= t2 + t3;
            u2 <= t4 + t5;
            u3 <= t6;
        end
    end

    // ---------------------------------------------------------------
    // Pipeline stage 4: sum pairs -> 2 sums (v0, v1)
    // v0=u0+u1, v1=u2+u3
    // ---------------------------------------------------------------
    reg [15:0] v0, v1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            v0 <= 16'd0; v1 <= 16'd0;
        end else begin
            v0 <= u0 + u1;
            v1 <= u2 + u3;
        end
    end

    // ---------------------------------------------------------------
    // Pipeline stage 5: final sum -> y
    // ---------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'd0;
        end else begin
            y <= v0 + v1;
        end
    end

endmodule