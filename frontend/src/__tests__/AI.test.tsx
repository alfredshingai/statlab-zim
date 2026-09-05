import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AI } from "../pages/AI";

describe("AI page", () => {
  it("renders pipeline description and inputs", () => {
    render(
      <MemoryRouter>
        <AI />
      </MemoryRouter>
    );
    expect(screen.getByText(/AI StatLab/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/dataset_id/)).toBeInTheDocument();
    expect(screen.getByText(/Ask \(full pipeline\)/)).toBeInTheDocument();
    expect(screen.getByText(/Cleaning assistant/)).toBeInTheDocument();
  });

  it("shows candidate disclaimer", () => {
    render(
      <MemoryRouter>
        <AI />
      </MemoryRouter>
    );
    expect(screen.getByText(/AI never calculates/)).toBeInTheDocument();
  });
});
