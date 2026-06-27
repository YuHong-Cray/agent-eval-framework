import React from "react";
import SignupForm from "./SignupForm";

function App() {
  const handleSubmit = (data) => console.log("Submitted:", data);
  return <SignupForm onSubmit={handleSubmit} loading={false} />;
}

export default App;
