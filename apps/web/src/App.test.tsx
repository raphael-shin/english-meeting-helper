import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders main panels", () => {
  render(<App />);
  expect(screen.getByText(/Quick Translate/i)).toBeInTheDocument();
  expect(screen.getByText(/AI Suggestions/i)).toBeInTheDocument();
});
