# Homebrew formula for Revibe
# 
# To use this formula, create a tap repository:
#   1. Create repo: github.com/webmyc/homebrew-revibe
#   2. Add this file as: Formula/revibe.rb
#
# Users can then install with:
#   brew tap webmyc/revibe
#   brew install revibe

class Revibe < Formula
  include Language::Python::Virtualenv

  desc "Codebase health scanner + AI-powered fixer for vibe-coded projects"
  homepage "https://revibe.help"
  url "https://files.pythonhosted.org/packages/source/r/revibe/revibe-0.1.0.tar.gz"
  # TODO: Update sha256 after publishing v0.1.0 to PyPI
  # Run: curl -sL https://files.pythonhosted.org/packages/source/r/revibe/revibe-0.1.0.tar.gz | shasum -a 256
  sha256 "PLACEHOLDER_UPDATE_AFTER_PYPI_RELEASE"
  license "MIT"

  depends_on "python@3.12"

  # Optional: Add rich for pretty output
  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-13.7.0.tar.gz"
    sha256 "REPLACE_WITH_RICH_SHA256"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    # Test that the CLI runs
    assert_match "revibe", shell_output("#{bin}/revibe --version")
    
    # Test scanning a minimal directory
    mkdir "test_project"
    (testpath/"test_project/test.py").write('print("hello")')
    
    output = shell_output("#{bin}/revibe scan #{testpath}/test_project 2>&1")
    assert_match "Health Score", output
  end
end
