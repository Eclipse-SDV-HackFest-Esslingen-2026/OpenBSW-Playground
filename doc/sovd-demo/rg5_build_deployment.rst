RG-5 — Build & Deployment
=========================

Requirements for building, packaging, and running the demo.

.. contents::
   :local:
   :depth: 1

.. req:: demo.sh provides one-command bring-up with --real-cda flag
   :id: REQ_RG5_001
   :status: done
   :tags: rg5, build, deployment
   :satisfies: SPEC_ARCH_BUILD

   ``demo.sh`` provides one-command bring-up with ``--real-cda`` flag.
   Sets up TAP, builds ECU, starts CDA Docker container.

.. req:: Multi-stage Docker build for CDA minimises image size
   :id: REQ_RG5_002
   :status: done
   :tags: rg5, build, docker
   :satisfies: SPEC_ARCH_BUILD

   Multi-stage Docker build for CDA minimises image size.
   cargo-chef + sccache for layer caching.

.. req:: Docker Compose orchestrates ECU + CDA + Grafana with profiles
   :id: REQ_RG5_003
   :status: done
   :tags: rg5, build, docker
   :satisfies: SPEC_ARCH_BUILD

   Docker Compose orchestrates ECU + CDA + Grafana with profiles.
   ``--profile stub-cda`` or ``--profile real-cda``.

.. req:: ECU build is reproducible from CMake preset
   :id: REQ_RG5_004
   :status: done
   :tags: rg5, build, cmake
   :satisfies: SPEC_ARCH_BUILD

   ECU build is reproducible from CMake preset.
   ``cmake --preset posix-freertos-sovd``.

.. req:: Demo runs in GitHub Codespaces with port forwarding
   :id: REQ_RG5_005
   :status: done
   :tags: rg5, deployment, codespaces
   :satisfies: SPEC_ARCH_BUILD

   Demo runs in GitHub Codespaces with port forwarding.
   ``demo.sh --codespaces`` mode.

.. req:: Demo runs locally on Ubuntu with sudo for TAP setup
   :id: REQ_RG5_006
   :status: done
   :tags: rg5, deployment, local
   :satisfies: SPEC_ARCH_BUILD

   Demo runs locally on Ubuntu with sudo for TAP setup.
   ``demo.sh --local`` or ``demo.sh --real-cda``.

.. req:: demo.sh --stop tears down all processes cleanly
   :id: REQ_RG5_007
   :status: done
   :tags: rg5, deployment
   :satisfies: SPEC_ARCH_BUILD

   ``demo.sh --stop`` tears down all processes cleanly.
   Kills ECU, CDA container, TAP interface.

.. req:: Live tmux status dashboard shows connection health
   :id: REQ_RG5_008
   :status: done
   :tags: rg5, deployment, observability
   :satisfies: SPEC_ARCH_BUILD

   Live tmux status dashboard shows connection health.
   ``demo.sh --live`` with auto-refresh.

.. req:: Pre-built CDA binary checked into repo via Git LFS
   :id: REQ_RG5_009
   :status: done
   :tags: rg5, build, deployment
   :satisfies: SPEC_ARCH_BUILD

   Pre-built CDA binary checked into repo via Git LFS.
   ``real-sovd-cda/bin/opensovd-cda`` (~26 MB, x86-64), Dockerfile supports
   ``USE_PREBUILT=1``.

.. req:: demo.sh auto-detects stub vs real CDA mode
   :id: REQ_RG5_010
   :status: done
   :tags: rg5, deployment
   :satisfies: SPEC_ARCH_BUILD

   ``demo.sh`` auto-detects stub vs real CDA mode.
   Checks for ``real-sovd-cda`` Docker container or stub PID file.
