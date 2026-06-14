`timescale 1ns/1ps
// Logic Analyzer (wide-sel) for the batched bitstream flow.
// Identical to la_axi.v but `sel` is SELW bits (default 6 -> up to 64 DUTs/batch).
//
// Register map (byte addresses, word-aligned):
//   0x00 CTRL   : bit0=arm/start, bit1=trigger_mode (0=sw-start,1=edge-trigger)
//                 bits[2+SELW-1:2] = sel (selects active DUT in this batch)
//   0x04 STATUS : bit0=done, bit1=armed
//   0x08 RADDR  : buffer read index
//   0x0C RDATA  : buffer[RADDR]
module la_axi_wide #(
    parameter DW    = 16,
    parameter DEPTH = 32768,
    parameter AW    = 15,
    parameter SELW  = 6
)(
    input  wire        S_AXI_ACLK,
    input  wire        S_AXI_ARESETN,
    input  wire [3:0]  S_AXI_AWADDR,
    input  wire        S_AXI_AWVALID,
    output reg         S_AXI_AWREADY,
    input  wire [31:0] S_AXI_WDATA,
    input  wire [3:0]  S_AXI_WSTRB,
    input  wire        S_AXI_WVALID,
    output reg  [1:0]  S_AXI_BRESP,
    output reg         S_AXI_BVALID,
    input  wire        S_AXI_BREADY,
    output reg         S_AXI_WREADY,
    input  wire [3:0]  S_AXI_ARADDR,
    input  wire        S_AXI_ARVALID,
    output reg         S_AXI_ARREADY,
    output reg  [31:0] S_AXI_RDATA,
    output reg  [1:0]  S_AXI_RRESP,
    output reg         S_AXI_RVALID,
    input  wire        S_AXI_RREADY,
    input  wire [DW-1:0]   probe,
    output wire [SELW-1:0] sel,
    output wire            capturing   // high while writing buffer -> reset-on-arm
);
    localparam IDLE=2'd0, ARMED=2'd1, CAPTURING=2'd2, DONE=2'd3;

    reg [DW-1:0] buffer [0:DEPTH-1];
    reg [AW-1:0] wr_addr;
    reg [1:0]    state;
    reg          done;
    reg          arm_pulse;
    reg          trig_mode;
    reg [SELW-1:0] sel_reg;

    assign sel = sel_reg;
    assign capturing = (state == CAPTURING);

    reg probe0_prev;
    wire rising_edge = probe[0] & ~probe0_prev;

    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) begin
            state<=IDLE; wr_addr<={AW{1'b0}}; done<=1'b0; probe0_prev<=1'b0;
        end else begin
            probe0_prev <= probe[0];
            case (state)
                IDLE:      if (arm_pulse) begin
                               done<=1'b0; wr_addr<={AW{1'b0}};
                               state <= trig_mode ? ARMED : CAPTURING;
                           end
                ARMED:     if (rising_edge) state <= CAPTURING;
                CAPTURING: begin
                               buffer[wr_addr] <= probe;
                               if (wr_addr == DEPTH-1) begin state<=DONE; done<=1'b1; end
                               else wr_addr <= wr_addr + 1'b1;
                           end
                // Re-arm from DONE so each sel sweep captures fresh data.
                DONE:      if (arm_pulse) begin
                               done<=1'b0; wr_addr<={AW{1'b0}};
                               state <= trig_mode ? ARMED : CAPTURING;
                           end
            endcase
        end
    end

    reg [AW-1:0] rd_index;
    wire [DW-1:0] buf_q = buffer[rd_index];
    wire wr_ok = S_AXI_AWVALID && S_AXI_WVALID && !S_AXI_BVALID;

    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) begin
            S_AXI_AWREADY<=0; S_AXI_WREADY<=0; S_AXI_BVALID<=0; S_AXI_BRESP<=0;
            rd_index<={AW{1'b0}}; arm_pulse<=0; trig_mode<=0; sel_reg<={SELW{1'b0}};
        end else begin
            arm_pulse <= 1'b0;
            if (wr_ok) begin
                S_AXI_AWREADY<=1; S_AXI_WREADY<=1;
                case (S_AXI_AWADDR[3:2])
                    2'd0: begin
                        if (S_AXI_WDATA[0]) arm_pulse <= 1'b1;
                        trig_mode <= S_AXI_WDATA[1];
                        sel_reg   <= S_AXI_WDATA[2+SELW-1:2];
                    end
                    2'd2: rd_index <= S_AXI_WDATA[AW-1:0];
                    default: ;
                endcase
                S_AXI_BVALID<=1; S_AXI_BRESP<=0;
            end else begin
                S_AXI_AWREADY<=0; S_AXI_WREADY<=0;
                if (S_AXI_BVALID && S_AXI_BREADY) S_AXI_BVALID<=0;
            end
        end
    end

    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) begin
            S_AXI_ARREADY<=0; S_AXI_RVALID<=0; S_AXI_RRESP<=0; S_AXI_RDATA<=0;
        end else begin
            if (S_AXI_ARVALID && !S_AXI_RVALID) begin
                S_AXI_ARREADY<=1;
                case (S_AXI_ARADDR[3:2])
                    2'd1: S_AXI_RDATA <= {30'd0, (state==ARMED), done};
                    2'd3: S_AXI_RDATA <= {{(32-DW){1'b0}}, buf_q};
                    default: S_AXI_RDATA <= 32'd0;
                endcase
                S_AXI_RVALID<=1; S_AXI_RRESP<=0;
            end else begin
                S_AXI_ARREADY<=0;
                if (S_AXI_RVALID && S_AXI_RREADY) S_AXI_RVALID<=0;
            end
        end
    end
endmodule
