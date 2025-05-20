"use client"

import type React from "react"

import { useState, useEffect } from "react"
import Image from "next/image"
import { Download, Loader2, Info, Twitter, Linkedin, Globe } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

// API base URL
const API_BASE_URL = "https://api.sofer.ai"

interface Site {
  name: string
  url: string
}

interface PreviewData {
  title: string
  downloadUrl: string
  fileFormat: string
  fileName: string
}

export default function Home() {
  const [url, setUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<PreviewData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [supportedSites, setSupportedSites] = useState<Site[]>([])
  const [loadingSites, setLoadingSites] = useState(false)

  // Fetch supported sites on component mount
  useEffect(() => {
    const fetchSupportedSites = async () => {
      setLoadingSites(true)
      try {
        const response = await fetch(`${API_BASE_URL}/v1/link/sites`)
        if (!response.ok) {
          throw new Error("Failed to fetch supported sites")
        }
        const data = await response.json()
        setSupportedSites(data)
      } catch (err) {
        console.error("Error fetching supported sites:", err)
      } finally {
        setLoadingSites(false)
      }
    }

    fetchSupportedSites()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!url) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/v1/link/extract`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      })

      if (!response.ok) {
        throw new Error(`API responded with status: ${response.status}`)
      }

      const data = await response.json()

      setPreview({
        title: data.title,
        downloadUrl: data.download_url,
        fileFormat: data.file_format,
        fileName: data.file_name,
      })
    } catch (err) {
      setError("Failed to process this URL. Please make sure it's from a supported Jewish media site.")
      setPreview(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#FCF6EC] flex flex-col">
      <header className="container mx-auto py-6 px-4">
        <div className="flex items-center gap-2">
          <Image src="/images/feather-logo.png" alt="Torah-dl Logo" width={40} height={40} className="h-10 w-auto" />
          <h1 className="text-3xl font-serif italic">Torah-dl</h1>
        </div>
      </header>

      <main className="container mx-auto flex-1 px-4 py-8 max-w-4xl">
        <div className="mb-8 text-center">
          <h2 className="text-2xl font-bold mb-2">Download Jewish Media Content</h2>
          <p className="text-gray-700 max-w-2xl mx-auto">
            Enter a link from a supported Jewish media site to get a direct download link for the audio or video. Click
            the info icon to see all supported sites.
          </p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-8">
          <div className="space-y-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <Input
                    type="url"
                    placeholder="Enter media URL (e.g., https://alldaf.org/p/225726)"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="pr-10"
                    required
                  />
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="ghost" size="icon" className="absolute right-0 top-0 h-full w-10 rounded-l-none">
                        <Info className="h-4 w-4" />
                        <span className="sr-only">Supported sites</span>
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-80 max-h-80 overflow-auto">
                      <div className="space-y-2">
                        <h4 className="font-medium">Supported Sites</h4>
                        {loadingSites ? (
                          <div className="flex items-center justify-center py-4">
                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            Loading...
                          </div>
                        ) : (
                          <ul className="text-sm space-y-1">
                            {supportedSites.map((site) => (
                              <li key={site.url}>
                                <a
                                  href={site.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-[#1E3A8A] hover:underline"
                                >
                                  {site.name}
                                </a>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </PopoverContent>
                  </Popover>
                </div>
                <Button type="submit" className="bg-[#1E3A8A] hover:bg-[#1E3A8A]/90" disabled={loading || !url}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Processing
                    </>
                  ) : (
                    "Get Download Link"
                  )}
                </Button>
              </div>
            </form>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {preview && (
              <Card className="p-4 border border-gray-200">
                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium text-lg">{preview.title}</h3>
                    <p className="text-sm text-gray-500">Format: {preview.fileFormat}</p>
                  </div>

                  <a
                    href={preview.downloadUrl}
                    download={preview.fileName}
                    className="bg-[#1E3A8A] text-white px-4 py-2 rounded-md hover:bg-[#1E3A8A]/90 transition-colors inline-flex items-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    Download {preview.fileFormat.includes("audio") ? "Audio" : "Video"}
                  </a>
                </div>
              </Card>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-8">
          <h3 className="font-medium mb-4 text-center">Support this project</h3>
          <div className="flex justify-center h-[150px] overflow-hidden">
            <iframe
              src="https://github.com/sponsors/SoferAi/card"
              title="Sponsor SoferAi"
              height="150"
              width="600"
              style={{ border: 0 }}
            />
          </div>
        </div>

        {/* Keep in Touch card */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-8">
          <h3 className="font-medium mb-6 text-center">Keep in Touch</h3>
          <div className="flex justify-center gap-8">
            <a
              href="https://x.com/Sofer_Ai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col items-center gap-2 text-gray-700 hover:text-[#1E3A8A] transition-colors"
              aria-label="Follow us on X (Twitter)"
            >
              <div className="bg-gray-100 p-3 rounded-full">
                <Twitter className="h-6 w-6" />
              </div>
              <span className="text-sm">@Sofer_Ai</span>
            </a>
            <a
              href="https://sofer.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col items-center gap-2 text-gray-700 hover:text-[#1E3A8A] transition-colors"
              aria-label="Visit our website"
            >
              <div className="bg-gray-100 p-3 rounded-full">
                <Globe className="h-6 w-6" />
              </div>
              <span className="text-sm">sofer.ai</span>
            </a>
            <a
              href="https://www.linkedin.com/company/soferai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col items-center gap-2 text-gray-700 hover:text-[#1E3A8A] transition-colors"
              aria-label="Connect with us on LinkedIn"
            >
              <div className="bg-gray-100 p-3 rounded-full">
                <Linkedin className="h-6 w-6" />
              </div>
              <span className="text-sm">LinkedIn</span>
            </a>
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-200 py-6 px-4 text-center text-sm text-gray-600">
        <p>© {new Date().getFullYear()} Sofer.Ai. All rights reserved.</p>
      </footer>
    </div>
  )
}
