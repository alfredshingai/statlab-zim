import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Reports } from "../pages/Reports";

describe("Reports page", () => {
  it("renders AI report preview", () => {
    render(
      <MemoryRouter>
        <Reports />
      </MemoryRouter>
    );
    expect(screen.getByText(/Report downloads/)).toBeInTheDocument();
    expect(screen.getByText(/Generate AI Report/)).toBeInTheDocument();
  });
});
