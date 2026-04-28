RG-5 Tests — Build & Deployment
================================

Test cases for build, packaging, and deployment.

.. contents::
   :local:
   :depth: 1

.. test:: demo.sh one-command bring-up with --real-cda
   :id: TEST_RG5_001
   :status: manual
   :tags: rg5, build, deployment
   :tests: REQ_RG5_001

   Run ``demo.sh --real-cda``. Verify TAP interface is created, ECU process
   starts, CDA Docker container is running, and health checks pass.

.. test:: Multi-stage Docker build produces minimal image
   :id: TEST_RG5_002
   :status: manual
   :tags: rg5, docker
   :tests: REQ_RG5_002

   Build CDA Docker image. Verify multi-stage build completes. Verify final
   image size is reasonable (< 200 MB).

.. test:: Docker Compose orchestration with profiles
   :id: TEST_RG5_003
   :status: manual
   :tags: rg5, docker
   :tests: REQ_RG5_003

   ``docker compose --profile stub-cda up`` starts stub CDA stack.
   ``docker compose --profile real-cda up`` starts real CDA stack.
   Verify only profile-specific services are started.

.. test:: ECU build from CMake preset is reproducible
   :id: TEST_RG5_004
   :status: manual
   :tags: rg5, cmake, build
   :tests: REQ_RG5_004

   Run ``cmake --preset posix-freertos-sovd`` followed by build. Verify
   ``app.sovdDemo.elf`` is produced. Clean and rebuild; verify identical output.

.. test:: Demo runs in GitHub Codespaces
   :id: TEST_RG5_005
   :status: manual
   :tags: rg5, codespaces
   :tests: REQ_RG5_005

   In a Codespace environment, run ``demo.sh --codespaces``. Verify port
   forwarding is configured for ports 8080 and 3000. Verify services are
   accessible via forwarded URLs.

.. test:: Demo runs locally on Ubuntu
   :id: TEST_RG5_006
   :status: manual
   :tags: rg5, local
   :tests: REQ_RG5_006

   On Ubuntu host, run ``demo.sh --local``. Verify sudo TAP setup succeeds.
   Verify ECU and CDA start successfully.

.. test:: demo.sh --stop tears down cleanly
   :id: TEST_RG5_007
   :status: manual
   :tags: rg5, deployment
   :tests: REQ_RG5_007

   Start demo, then run ``demo.sh --stop``. Verify ECU process is terminated,
   CDA container is stopped/removed, TAP interface is deleted. Verify no
   orphan processes remain.

.. test:: Live tmux status dashboard
   :id: TEST_RG5_008
   :status: manual
   :tags: rg5, deployment
   :tests: REQ_RG5_008

   Run ``demo.sh --live``. Verify tmux session is created. Verify status
   dashboard refreshes automatically showing connection health.

.. test:: Pre-built CDA binary works with USE_PREBUILT
   :id: TEST_RG5_009
   :status: manual
   :tags: rg5, deployment
   :tests: REQ_RG5_009

   Verify ``real-sovd-cda/bin/opensovd-cda`` exists (~26 MB, x86-64).
   Build Docker image with ``USE_PREBUILT=1``. Verify CDA starts and
   passes health check.

.. test:: demo.sh auto-detects CDA mode
   :id: TEST_RG5_010
   :status: manual
   :tags: rg5, deployment
   :tests: REQ_RG5_010

   Start with real CDA container running. Run ``demo.sh --status``. Verify
   output indicates real CDA mode. Stop real CDA, start stub CDA. Verify
   mode detection switches.
