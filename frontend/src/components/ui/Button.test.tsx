import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Button from "./Button";

describe("Button", () => {
  it("renders its children", () => {
    render(<Button>שלח</Button>);
    expect(screen.getByText("שלח")).toBeInTheDocument();
  });

  it("calls onClick when clicked", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>לחץ</Button>);
    fireEvent.click(screen.getByText("לחץ"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("is disabled when the disabled prop is set", () => {
    render(<Button disabled>מנוטרל</Button>);
    expect(screen.getByText("מנוטרל")).toBeDisabled();
  });
});
