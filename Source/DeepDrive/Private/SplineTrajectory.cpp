// 

#include "DeepDrive.h"
#include "SplineTrajectory.h"


// Sets default values
ASplineTrajectory::ASplineTrajectory()
{
 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;


	Trajectory = CreateDefaultSubobject<USplineComponent>(TEXT("Trajectory"));
	// Mesh->SetupAttachment(RootComponent);
	RootComponent = Trajectory;
}

// Called when the game starts or when spawned
void ASplineTrajectory::BeginPlay()
{
	Super::BeginPlay();
	
}

// Called every frame
void ASplineTrajectory::Tick( float DeltaTime )
{
	Super::Tick( DeltaTime );

}

