import { describe, expect, it } from "vitest";
import { dayMonth, timelineScale } from "./timeline";

describe("timelineScale", () => {
  const scale = timelineScale(["2022-09-07", "2022-10-23", "2022-10-30", "2023-01-08"]);

  it("conta os dias do primeiro ao último evento", () => {
    expect(scale.days).toBe(123);
  });

  it("põe o primeiro evento em 0 e o último em 1", () => {
    expect(scale.at("2022-09-07")).toBe(0);
    expect(scale.at("2023-01-08")).toBe(1);
  });

  it("posiciona as datas do meio na proporção do tempo", () => {
    expect(scale.at("2022-10-23")).toBeCloseTo(46 / 123, 6);
    expect(scale.at("2023-01-01")).toBeCloseTo(116 / 123, 6);
  });
});

describe("dayMonth", () => {
  it("formata a data como dia/mês sem zero à esquerda", () => {
    expect(dayMonth("2023-01-08")).toBe("8/1");
    expect(dayMonth("2022-10-30")).toBe("30/10");
  });
});
