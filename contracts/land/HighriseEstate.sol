// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import "@openzeppelin-upgradeable/contracts/token/ERC721/ERC721Upgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721EnumerableUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721RoyaltyUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/utils/ERC721HolderUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/utils/introspection/ERC165Checker.sol";

import "../../interfaces/IHighriseLand.sol";

function parseToCoordinates(uint256 tokenId) pure returns (uint256[2] memory) {
    return [tokenId >> 16, tokenId & 0xFFFF];
}

contract HighriseEstate is
    Initializable,
    ERC721Upgradeable,
    ERC721EnumerableUpgradeable,
    ERC721HolderUpgradeable,
    ERC721RoyaltyUpgradeable
{
    using ERC165Checker for address;
    using Counters for Counters.Counter;

    // ------------------------ STORAGE --------------------------------------
    string private _baseTokenURI;
    address private _land;
    Counters.Counter private _tokenIds;
    mapping(uint256 => uint256[]) public estatesToParcels;

    // -----------------------------------------------------------------------

    // ------------------------ INITIALIZER -----------------------------------
    function initialize(
        string memory name,
        string memory symbol,
        string memory baseTokenURI,
        address land
    ) public virtual initializer {
        require(
            land.supportsInterface(type(IHighriseLand).interfaceId),
            "IS_NOT_HIGHRISE_LAND_CONTRACT"
        );
        require(
            land.supportsInterface(type(IERC721).interfaceId),
            "IS_NOT_ERC721_CONTRACT"
        );
        __HighriseEstate_init(name, symbol, baseTokenURI, land);
    }

    function __HighriseEstate_init(
        string memory name,
        string memory symbol,
        string memory baseTokenURI,
        address land
    ) internal onlyInitializing {
        __ERC721_init(name, symbol);
        __ERC721Enumerable_init();
        __ERC721Holder_init();
        __HighriseEstate_init_unchained(name, symbol, baseTokenURI, land);
    }

    function __HighriseEstate_init_unchained(
        string memory,
        string memory,
        string memory baseTokenURI,
        address land
    ) internal onlyInitializing {
        _baseTokenURI = baseTokenURI;
        _land = land;
        _setDefaultRoyalty(msg.sender, 300);
    }

    // ------------------------------------------------------------------------

    /**
     * @dev Token URIs will be autogenerated based on `baseURI` and their token IDs.
     * See {ERC721-tokenURI}.
     */
    function _baseURI() internal view virtual override returns (string memory) {
        return _baseTokenURI;
    }

    /**
    The expected array shape is:
     | ----------   x
     | [0  1  2]
     | [3  4  5]
     | [6  7  8]
     y
     */
    function _isEstateShapeValid(uint256[] memory parcelIds) internal {
        uint256 size = 0;
        if (parcelIds.length == 9) {
            // We expect a 3x3 matrix.
            size = 3;
        } else if (parcelIds.length == 36) {
            size = 6;
        } else if (parcelIds.length == 81) {
            size = 9;
        } else if (parcelIds.length == 144) {
            size = 12;
        } else {
            require(false, "Invalid estate shape");
        }
        // For each row,
        for (uint256 y = 0; y < 3; y++) {
            // For the first two X's,
            for (uint256 x = 0; x < 2; x++) {
                uint256 left = parcelIds[y * 3 + x];
                uint256 right = parcelIds[y * 3 + x + 1];
                require(
                    parseToCoordinates(left)[0] + 1 ==
                        parseToCoordinates(right)[0]
                );
            }
        }

        // For each column,
        for (uint256 x = 0; x < size; x++) {
            // For the first two Y's,
            for (uint256 y = 0; y < size - 1; y++) {
                uint256 upper = parcelIds[y * 3 + x];
                uint256 lower = parcelIds[(y + 1) * 3 + x];
                require(
                    (parseToCoordinates(upper)[1] + 1) ==
                        parseToCoordinates(lower)[1]
                );
            }
        }
    }

    function mintFromParcels(uint256[] memory tokenIds)
        public
        returns (uint256)
    {
        _isEstateShapeValid(tokenIds);
        IHighriseLand(_land).bindToEstate(msg.sender, tokenIds);
        _tokenIds.increment();
        uint256 tokenId = _tokenIds.current();
        estatesToParcels[tokenId] = tokenIds;
        _mint(msg.sender, tokenId);
        return tokenId;
    }

    function burn(uint256 tokenId) public {
        require(
            _exists(tokenId),
            "ERC721: operator query for nonexistent token"
        );
        require(
            _isApprovedOrOwner(msg.sender, tokenId),
            "ERC721Burnable: caller is not owner nor approved"
        );
        uint256[] memory parcels = estatesToParcels[tokenId];
        for (uint256 i = 0; i < parcels.length; i++) {
            IERC721(_land).safeTransferFrom(
                address(this),
                msg.sender,
                parcels[i]
            );
        }
        _burn(tokenId);
    }

    // --------------------------------------- OVERRIDES ---------------------------------------------
    // The following functions are overrides required by Solidity.
    function _burn(uint256 tokenId)
        internal
        override(ERC721Upgradeable, ERC721RoyaltyUpgradeable)
    {
        super._burn(tokenId);
    }

    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId
    ) internal override(ERC721Upgradeable, ERC721EnumerableUpgradeable) {
        super._beforeTokenTransfer(from, to, tokenId);
    }

    /**
     * @dev See {IERC165-supportsInterface}.
     */
    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual
        override(
            ERC721Upgradeable,
            ERC721EnumerableUpgradeable,
            ERC721RoyaltyUpgradeable
        )
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    // -----------------------------------------------------------------------------------------------

    // ----------------------- HELPER LOGIC --------------------------------------------
    function ownerTokens(address owner) public view returns (uint256[] memory) {
        uint256 balance = balanceOf(owner);
        uint256[] memory tokens = new uint256[](balance);

        for (uint256 i = 0; i < balance; i++) {
            tokens[i] = tokenOfOwnerByIndex(owner, i);
        }

        return tokens;
    }
    // ---------------------------------------------------------------------------------
}
