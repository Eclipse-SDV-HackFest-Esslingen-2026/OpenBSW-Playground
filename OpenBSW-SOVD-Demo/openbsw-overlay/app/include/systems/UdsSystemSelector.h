// Copyright 2025 Accenture.
// FLXC1000 ECU selector - conditionally uses UdsSystem or Flxc1000UdsSystem

#pragma once

#ifdef USE_FLXC1000_ECU
#include "systems/Flxc1000UdsSystem.h"
namespace uds
{
using UdsSystem = Flxc1000UdsSystem;
}
#else
#include "systems/UdsSystem.h"
// UdsSystem is already in namespace uds
#endif
